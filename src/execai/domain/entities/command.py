"""
Command entity - Represents a system command to be executed.

This module defines the Command entity which encapsulates all information
about a system command including its execution context and security.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


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
    
    model_config = ConfigDict(use_enum_values=True)
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    original_request: str = Field(description="Original request")
    parsed_command: str = Field(description="Parsed system command")
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
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Last update timestamp"
    )
    executed_at: Optional[datetime] = Field(
        None, description="Execution timestamp"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Completion timestamp"
    )
    
    # Results
    exit_code: Optional[int] = Field(
        None, description="Command exit code"
    )
    stdout: Optional[str] = Field(
        None, description="Standard output"
    )
    stderr: Optional[str] = Field(
        None, description="Standard error"
    )
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds"
    )
    
    # Relationships
    schedule_id: Optional[UUID] = Field(
        None, description="Associated schedule ID"
    )
    parent_command_id: Optional[UUID] = Field(
        None, description="Parent command ID"
    )

    @field_validator('parsed_command')
    @classmethod
    def validate_parsed_command(cls, v: str) -> str:
        """Validate that parsed command is not empty."""
        if not v or not v.strip():
            raise ValueError("Parsed command cannot be empty")
        return v.strip()
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def set_updated_at(cls, v) -> datetime:
        """Set updated_at to current time."""
        return datetime.now(timezone.utc)
    
    def is_safe_command(self) -> bool:
        """Check if command is safe to execute."""
        dangerous_commands = [
            "rm", "rmdir", "del", "delete", "format", "fdisk",
            "mkfs", "dd", "shutdown", "reboot", "halt", "poweroff",
            "kill", "killall", "pkill", "sudo", "su", "chmod 777",
            "chown", "passwd", "userdel", "groupdel", "iptables",
            "ufw", "firewall", "netsh", "registry", "regedit",
            "systemctl", "service", "launchctl", "crontab -r",
            "history -c", "truncate", "shred", "wipe", "secure-delete"
        ]
        
        command_lower = self.parsed_command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return False
        return True
    
    def can_execute(self) -> bool:
        """Check if command can be executed."""
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
        self.executed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def complete_execution(
        self, exit_code: int, stdout: str = "", stderr: str = "", 
        execution_time: float = 0.0
    ) -> None:
        """Mark command as completed."""
        if self.status != CommandStatus.RUNNING:
            raise ValueError("Command is not running")
        
        self.status = (
            CommandStatus.COMPLETED if exit_code == 0 else CommandStatus.FAILED
        )
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.execution_time = execution_time
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def cancel_execution(self) -> None:
        """Cancel command execution."""
        if self.status not in [CommandStatus.PENDING, CommandStatus.RUNNING]:
            raise ValueError("Command cannot be cancelled")
        
        self.status = CommandStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert command to dictionary."""
        return self.model_dump()
    
    def __str__(self) -> str:
        """String representation of command."""
        return f"Command({self.id}): {self.parsed_command[:50]}..."
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Command(id={self.id}, status={self.status}, "
            f"command='{self.parsed_command}')"
        ) 