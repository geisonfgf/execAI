"""
ExecutionResult entity - Represents the result of command execution.

This module defines the ExecutionResult entity which tracks
the outcome of command execution including metrics and logs.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class ExecutionResult(BaseModel):
    """
    ExecutionResult entity representing the result of command execution.
    
    This entity tracks the outcome of command execution including
    performance metrics, output, and error information.
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    command_id: UUID = Field(description="Associated command ID")
    schedule_id: Optional[UUID] = Field(
        None, description="Associated schedule ID"
    )
    
    # Execution details
    started_at: datetime = Field(description="Execution start time")
    completed_at: Optional[datetime] = Field(
        None, description="Execution end time"
    )
    duration: Optional[float] = Field(
        None, description="Execution duration"
    )
    
    # Results
    success: bool = Field(default=False, description="Execution success")
    exit_code: Optional[int] = Field(
        None, description="Process exit code"
    )
    stdout: Optional[str] = Field(None, description="Standard output")
    stderr: Optional[str] = Field(None, description="Standard error")
    
    # Metrics
    memory_usage: Optional[float] = Field(
        None, description="Memory usage in MB"
    )
    cpu_usage: Optional[float] = Field(
        None, description="CPU usage percentage"
    )
    
    # Metadata
    environment: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    working_directory: Optional[str] = Field(
        None, description="Working directory"
    )

    def calculate_duration(self) -> Optional[float]:
        """Calculate execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.success and (self.exit_code is None or self.exit_code == 0)
    
    def has_output(self) -> bool:
        """Check if execution produced output."""
        return bool(self.stdout)
    
    def has_errors(self) -> bool:
        """Check if execution produced errors."""
        return bool(self.stderr)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return self.model_dump()
    
    def __str__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"ExecutionResult({self.id}): {status}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"ExecutionResult(id={self.id}, success={self.success}, "
            f"exit_code={self.exit_code})"
        ) 