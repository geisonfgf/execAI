"""
Command Agent - LangGraph-based agent for command interpretation.

This module implements a LangGraph agent that processes natural language
requests and converts them into system commands with scheduling information.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ...domain.entities.command import Command, CommandType
from ...domain.entities.schedule import Schedule, ScheduleType
from ..config import settings


class CommandInterpretation(BaseModel):
    """Parsed command interpretation."""
    
    original_request: str = Field(description="Original user request")
    parsed_commands: List[str] = Field(description="Parsed system commands")
    command_type: CommandType = Field(description="Type of command")
    schedule_info: Optional[Dict[str, Any]] = Field(
        None, description="Schedule information"
    )
    reasoning: str = Field(description="Reasoning for the interpretation")
    safety_assessment: str = Field(description="Safety assessment")
    requires_confirmation: bool = Field(description="Requires user confirmation")


class AgentState(TypedDict):
    """State of the command agent."""
    
    user_request: str
    messages: List[BaseMessage]
    interpretation: Optional[CommandInterpretation]
    commands: List[Command]
    schedule: Optional[Schedule]
    errors: List[str]
    requires_confirmation: bool


class CommandAgent:
    """
    LangGraph-based agent for command interpretation and scheduling.
    
    This agent processes natural language requests and converts them into
    executable system commands with appropriate scheduling information.
    """
    
    def __init__(self) -> None:
        """Initialize the command agent."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            api_key=settings.openai_api_key,
        )
        
        self.parser = PydanticOutputParser(pydantic_object=CommandInterpretation)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("interpret_request", self._interpret_request)
        workflow.add_node("safety_check", self._safety_check)
        workflow.add_node("create_commands", self._create_commands)
        workflow.add_node("create_schedule", self._create_schedule)
        workflow.add_node("finalize", self._finalize)
        
        # Add edges
        workflow.set_entry_point("interpret_request")
        workflow.add_edge("interpret_request", "safety_check")
        workflow.add_edge("safety_check", "create_commands")
        workflow.add_edge("create_commands", "create_schedule")
        workflow.add_edge("create_schedule", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _interpret_request(self, state: AgentState) -> AgentState:
        """Interpret the user request."""
        system_prompt = f"""
        You are an AI assistant that interprets natural language requests 
        and converts them into system commands. 
        
        Your task is to:
        1. Parse the user's request into specific system commands
        2. Identify if this is a one-time or scheduled task
        3. Extract timing information if present
        4. Assess the safety of the commands
        5. Determine if user confirmation is needed
        
        Safe commands include: {', '.join(settings.allowed_commands)}
        
        {self.parser.get_format_instructions()}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_request"])
        ]
        
        try:
            response = self.llm(messages)
            interpretation = self.parser.parse(response.content)
            
            state["messages"] = messages + [response]
            state["interpretation"] = interpretation
            
        except Exception as e:
            state["errors"].append(f"Request interpretation failed: {str(e)}")
        
        return state
    
    def _safety_check(self, state: AgentState) -> AgentState:
        """Perform safety checks on the interpreted commands."""
        if not state["interpretation"]:
            state["errors"].append("No interpretation available for safety check")
            return state
        
        interpretation = state["interpretation"]
        dangerous_commands = []
        
        for command in interpretation.parsed_commands:
            if not settings.is_safe_command(command):
                dangerous_commands.append(command)
        
        if dangerous_commands and settings.safe_mode:
            state["errors"].append(
                f"Dangerous commands detected in safe mode: {dangerous_commands}"
            )
            return state
        
        # Update confirmation requirement
        if dangerous_commands or interpretation.requires_confirmation:
            state["requires_confirmation"] = True
        
        return state
    
    def _create_commands(self, state: AgentState) -> AgentState:
        """Create Command entities from interpretation."""
        if not state["interpretation"]:
            state["errors"].append("No interpretation available for command creation")
            return state
        
        interpretation = state["interpretation"]
        commands = []
        
        for parsed_command in interpretation.parsed_commands:
            command = Command(
                original_request=interpretation.original_request,
                parsed_command=parsed_command,
                command_type=interpretation.command_type,
                requires_confirmation=state["requires_confirmation"],
                safe_mode=settings.safe_mode,
                allowed_in_safe_mode=settings.is_safe_command(parsed_command),
                timeout=settings.max_execution_time,
            )
            commands.append(command)
        
        state["commands"] = commands
        return state
    
    def _create_schedule(self, state: AgentState) -> AgentState:
        """Create Schedule entity if needed."""
        if not state["interpretation"]:
            return state
        
        interpretation = state["interpretation"]
        schedule_info = interpretation.schedule_info
        
        if not schedule_info:
            return state
        
        try:
                         schedule = Schedule(
                 name=f"Schedule for: {interpretation.original_request}",
                 description="Auto-generated schedule for command execution",
                schedule_type=ScheduleType(schedule_info.get("type", "once")),
                cron_expression=schedule_info.get("cron_expression"),
                start_time=self._parse_time(schedule_info.get("start_time")),
                end_time=self._parse_time(schedule_info.get("end_time")),
                max_executions=schedule_info.get("max_executions"),
                max_retries=schedule_info.get("max_retries", 3),
                command_template={
                    "original_request": interpretation.original_request,
                    "parsed_commands": interpretation.parsed_commands,
                }
            )
            
            # Update next run time
            schedule.update_next_run()
            
            state["schedule"] = schedule
            
            # Link commands to schedule
            for command in state["commands"]:
                command.schedule_id = schedule.id
                
        except Exception as e:
            state["errors"].append(f"Schedule creation failed: {str(e)}")
        
        return state
    
    def _finalize(self, state: AgentState) -> AgentState:
        """Finalize the agent processing."""
        if state["errors"]:
            return state
        
        # Final validation
        if not state["commands"]:
            state["errors"].append("No commands were created")
        
        return state
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """Parse time string to datetime."""
        if not time_str:
            return None
        
        try:
            # Try parsing ISO format
            return datetime.fromisoformat(time_str)
        except ValueError:
            # Try parsing relative time
            if "in" in time_str.lower():
                # Simple relative time parsing
                if "minute" in time_str:
                    minutes = int(''.join(filter(str.isdigit, time_str)))
                    return datetime.utcnow() + timedelta(minutes=minutes)
                elif "hour" in time_str:
                    hours = int(''.join(filter(str.isdigit, time_str)))
                    return datetime.utcnow() + timedelta(hours=hours)
                elif "day" in time_str:
                    days = int(''.join(filter(str.isdigit, time_str)))
                    return datetime.utcnow() + timedelta(days=days)
        
        return None
    
    def process_request(self, user_request: str) -> AgentState:
        """Process a user request and return the agent state."""
        initial_state: AgentState = {
            "user_request": user_request,
            "messages": [],
            "interpretation": None,
            "commands": [],
            "schedule": None,
            "errors": [],
            "requires_confirmation": settings.confirmation_required,
        }
        
        try:
            result = self.graph.invoke(initial_state)
            return result
        except Exception as e:
            initial_state["errors"].append(f"Agent processing failed: {str(e)}")
            return initial_state
    
    def get_command_summary(self, state: AgentState) -> str:
        """Generate a summary of the commands to be executed."""
        if state["errors"]:
            return f"Errors occurred: {'; '.join(state['errors'])}"
        
        if not state["commands"]:
            return "No commands were generated."
        
        summary = []
        summary.append(f"Generated {len(state['commands'])} command(s):")
        
        for i, command in enumerate(state["commands"], 1):
            summary.append(f"{i}. {command.parsed_command}")
        
        if state["schedule"]:
            schedule = state["schedule"]
            summary.append(f"\nSchedule: {schedule.schedule_type}")
            if schedule.cron_expression:
                summary.append(f"Cron: {schedule.cron_expression}")
            if schedule.next_run:
                summary.append(f"Next run: {schedule.next_run}")
        
        if state["requires_confirmation"]:
            summary.append("\n⚠️  User confirmation required before execution.")
        
        return "\n".join(summary) 