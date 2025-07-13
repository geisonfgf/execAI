"""
Schedule entity - Represents a scheduled or recurring task.

This module defines the Schedule entity which manages the timing and execution
of commands including one-time schedules, recurring tasks, and cron-based 
schedules.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4

from croniter import croniter
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ScheduleType(str, Enum):
    """Enumeration of schedule types."""
    
    ONCE = "once"
    RECURRING = "recurring"
    CRON = "cron"


class ScheduleStatus(str, Enum):
    """Enumeration of schedule statuses."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Schedule(BaseModel):
    """
    Schedule entity representing a scheduled or recurring task.
    
    This entity manages the timing and execution of commands including
    one-time schedules, recurring tasks, and cron-based schedules.
    """
    
    model_config = ConfigDict(use_enum_values=True)
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    schedule_type: ScheduleType = Field(
        default=ScheduleType.ONCE, 
        description="Type of schedule"
    )
    status: ScheduleStatus = Field(
        default=ScheduleStatus.ACTIVE, 
        description="Current status"
    )
    
    # Timing
    cron_expression: Optional[str] = Field(
        None, description="Cron expression"
    )
    start_time: Optional[datetime] = Field(
        None, description="Start time"
    )
    end_time: Optional[datetime] = Field(
        None, description="End time"
    )
    next_run: Optional[datetime] = Field(
        None, description="Next run time"
    )
    last_run: Optional[datetime] = Field(
        None, description="Last run time"
    )
    
    # Configuration
    max_executions: Optional[int] = Field(
        None, description="Max executions"
    )
    execution_count: int = Field(
        default=0, description="Current execution count"
    )
    retry_count: int = Field(
        default=0, description="Retry attempts"
    )
    max_retries: int = Field(
        default=3, description="Maximum retries"
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
    
    # Relationships
    command_template: Dict[str, str] = Field(
        default_factory=dict, description="Command template"
    )

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, v: Optional[str]) -> Optional[str]:
        """Validate cron expression format."""
        if v is None:
            return v
        
        try:
            croniter(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
    
    @field_validator('max_executions')
    @classmethod
    def validate_max_executions(cls, v: Optional[int]) -> Optional[int]:
        """Validate max executions is positive."""
        if v is not None and v <= 0:
            raise ValueError("Max executions must be positive")
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries is non-negative."""
        if v < 0:
            raise ValueError("Max retries must be non-negative")
        return v
    
    @field_validator('updated_at', mode='before')
    @classmethod
    def set_updated_at(cls, v) -> datetime:
        """Set updated_at to current time."""
        return datetime.now(timezone.utc)
    
    def is_active(self) -> bool:
        """Check if schedule is active."""
        return self.status == ScheduleStatus.ACTIVE
    
    def should_execute(self) -> bool:
        """Check if schedule should execute now."""
        if not self.is_active():
            return False
        
        if self.max_executions is not None:
            if self.execution_count >= self.max_executions:
                return False
        
        if self.next_run is None:
            return False
        
        return datetime.now(timezone.utc) >= self.next_run
    
    def calculate_next_run(self) -> Optional[datetime]:
        """Calculate the next run time based on schedule type."""
        if self.schedule_type == ScheduleType.ONCE:
            return self.start_time
        
        if self.schedule_type == ScheduleType.CRON and self.cron_expression:
            try:
                cron = croniter(
                    self.cron_expression, datetime.now(timezone.utc)
                )
                return cron.get_next(datetime)
            except ValueError:
                return None
        
        return None
    
    def update_next_run(self) -> None:
        """Update the next run time."""
        self.next_run = self.calculate_next_run()
    
    def increment_execution_count(self) -> None:
        """Increment the execution count."""
        self.execution_count += 1
        self.last_run = datetime.now(timezone.utc)
        self.update_next_run()
        
        if (self.max_executions is not None and 
                self.execution_count >= self.max_executions):
            self.status = ScheduleStatus.COMPLETED
    
    def increment_retry_count(self) -> None:
        """Increment the retry count."""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = ScheduleStatus.FAILED
    
    def reset_retry_count(self) -> None:
        """Reset the retry count."""
        self.retry_count = 0
    
    def has_retries_left(self) -> bool:
        """Check if there are retries left."""
        return self.retry_count < self.max_retries
    
    def pause(self) -> None:
        """Pause the schedule."""
        if self.status == ScheduleStatus.ACTIVE:
            self.status = ScheduleStatus.PAUSED
    
    def resume(self) -> None:
        """Resume the schedule."""
        if self.status == ScheduleStatus.PAUSED:
            self.status = ScheduleStatus.ACTIVE
            self.update_next_run()
    
    def complete(self) -> None:
        """Mark schedule as completed."""
        self.status = ScheduleStatus.COMPLETED
    
    def fail(self) -> None:
        """Mark schedule as failed."""
        self.status = ScheduleStatus.FAILED
    
    def to_dict(self) -> dict:
        """Convert schedule to dictionary."""
        return self.model_dump()
    
    def __str__(self) -> str:
        """String representation of schedule."""
        return f"Schedule({self.id}): {self.name}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Schedule(id={self.id}, name='{self.name}', "
            f"status={self.status}, type={self.schedule_type})"
        ) 