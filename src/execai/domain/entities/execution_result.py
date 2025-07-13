"""
ExecutionResult entity - Represents the result of command execution.

This module defines the ExecutionResult entity which tracks
the outcome of command execution including metrics and logs.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """
    ExecutionResult entity representing the result of command execution.
    
    This entity tracks the outcome of command execution including
    performance metrics, output, and error information.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    command_id: UUID = Field(description="Associated command ID")
    schedule_id: Optional[UUID] = Field(None, description="Associated schedule ID")
    
    # Execution details
    started_at: datetime = Field(description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution end time")
    duration: Optional[float] = Field(None, description="Execution duration")
    
    # Results
    success: bool = Field(default=False, description="Execution success")
    exit_code: Optional[int] = Field(None, description="Process exit code")
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    
    # Metrics
    memory_usage: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    
    # Metadata
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    working_directory: Optional[str] = Field(None, description="Working directory")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    
    def calculate_duration(self) -> Optional[float]:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None
    
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.success and (self.exit_code == 0 if self.exit_code is not None else True)
    
    def has_output(self) -> bool:
        """Check if execution produced output."""
        return bool(self.stdout and self.stdout.strip())
    
    def has_errors(self) -> bool:
        """Check if execution produced errors."""
        return bool(self.stderr and self.stderr.strip()) or not self.is_successful()
    
    def to_dict(self) -> dict:
        """Convert execution result to dictionary."""
        return dict(self)
    
    def __str__(self) -> str:
        """String representation of execution result."""
        status = "SUCCESS" if self.is_successful() else "FAILED"
        return f"ExecutionResult(id={self.id}, status={status})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"ExecutionResult(id={self.id}, command_id={self.command_id}, "
            f"success={self.success}, exit_code={self.exit_code})"
        ) 