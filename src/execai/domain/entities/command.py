"""
Command entity - Represents a system command to be executed.

This module defines the Command entity which encapsulates all information
about a system command including its execution context and security.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class CommandStatus(str, Enum):
    """Enumeration of possible command statuses."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandType(str, Enum):
    """Enumeration of command types."""
    
    SYSTEM = "system"
    SCRIPT = "script"
    SCHEDULED = "scheduled"
    CRON = "cron"


class Command(BaseModel):
    """
    Command entity representing a system command to be executed.
    
    This entity encapsulates all information about a system command including
    its execution context, security constraints, and execution metadata.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    original_request: str = Field(..., description="Original request")
    parsed_command: str = Field(..., description="Parsed system command")
    command_type: CommandType = Field(
        default=CommandType.SYSTEM, description="Type of command"
    )
    status: CommandStatus = Field(
        default=CommandStatus.PENDING, description="Current status"
    )
    
    # Execution context
    working_directory: Optional[str] = Field(
        None, description="Working directory for execution"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    timeout: int = Field(default=300, description="Timeout in seconds")
    
    # Security
    requires_confirmation: bool = Field(
        default=True, description="Requires user confirmation"
    )
    safe_mode: bool = Field(default=True, description="Run in safe mode")
    allowed_in_safe_mode: bool = Field(
        default=False, description="Safe to run in safe mode"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    executed_at: Optional[datetime] = Field(None, description="Execution timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    # Results
    exit_code: Optional[int] = Field(None, description="Command exit code")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    # Relationships
    schedule_id: Optional[UUID] = Field(None, description="Associated schedule ID")
    parent_command_id: Optional[UUID] = Field(None, description="Parent command ID")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    @validator('parsed_command')
    def validate_parsed_command(cls, v: str) -> str:
        """Validate that parsed command is not empty."""
        if not v or not v.strip():
            raise ValueError("Parsed command cannot be empty")
        return v.strip()
    
    @validator('timeout')
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v: datetime, values: dict) -> datetime:
        """Set updated_at to current time."""
        return datetime.utcnow()
    
    def is_safe_command(self) -> bool:
        """Check if command is safe to execute."""
        dangerous_commands = [
            'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd',
            'sudo', 'su', 'chmod', 'chown', 'passwd',
            'iptables', 'systemctl', 'service', 'kill',
            'pkill', 'killall', 'shutdown', 'reboot',
            'mount', 'umount', 'crontab'
        ]
        
        command_parts = self.parsed_command.split()
        if not command_parts:
            return False
            
        base_command = command_parts[0].lower()
        return base_command not in dangerous_commands
    
    def can_execute(self) -> bool:
        """Check if command can be executed based on current state."""
        if self.status != CommandStatus.PENDING:
            return False
        
        if self.safe_mode and not self.is_safe_command():
            return False
        
        return True
    
    def start_execution(self) -> None:
        """Mark command as running."""
        if not self.can_execute():
            raise ValueError("Command cannot be executed")
        
        self.status = CommandStatus.RUNNING
        self.executed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_execution(self, exit_code: int, stdout: str = "", stderr: str = "", 
                          execution_time: float = 0.0) -> None:
        """Mark command as completed with results."""
        if self.status != CommandStatus.RUNNING:
            raise ValueError("Command must be running to complete")
        
        self.status = CommandStatus.COMPLETED if exit_code == 0 else CommandStatus.FAILED
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel_execution(self) -> None:
        """Cancel command execution."""
        if self.status in [CommandStatus.COMPLETED, CommandStatus.FAILED]:
            raise ValueError("Cannot cancel completed command")
        
        self.status = CommandStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert command to dictionary."""
        return self.dict()
    
    def __str__(self) -> str:
        """String representation of command."""
        return f"Command(id={self.id}, cmd='{self.parsed_command}', status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Command(id={self.id}, original='{self.original_request}', "
                f"parsed='{self.parsed_command}', status={self.status})") 