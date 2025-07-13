"""
Cron Scheduler - Manage recurring tasks and scheduled job execution.

This module provides a cron-based scheduler for managing recurring
command execution and job scheduling.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

from ...domain.entities.schedule import Schedule, ScheduleStatus


logger = logging.getLogger(__name__)


class CronScheduler:
    """
    Cron-based scheduler for managing recurring tasks.
    
    This class manages scheduled jobs and executes them according to
    their cron expressions or timing configurations.
    """
    
    def __init__(self) -> None:
        """Initialize the cron scheduler."""
        self.schedules: Dict[str, Schedule] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.executor = None  # Will be injected
    
    def add_schedule(self, schedule: Schedule) -> None:
        """
        Add a schedule to the scheduler.
        
        Args:
            schedule: The schedule to add
        """
        if not schedule.is_active():
            logger.warning(f"Schedule {schedule.id} is not active, skipping")
            return
        
        # Calculate next run time
        schedule.update_next_run()
        
        self.schedules[str(schedule.id)] = schedule
        logger.info(f"Added schedule {schedule.id}: {schedule.name}")
    
    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a schedule from the scheduler.
        
        Args:
            schedule_id: ID of the schedule to remove
            
        Returns:
            True if schedule was removed, False if not found
        """
        if schedule_id in self.schedules:
            schedule = self.schedules.pop(schedule_id)
            logger.info(f"Removed schedule {schedule_id}: {schedule.name}")
            return True
        return False
    
    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        return self.schedules.get(schedule_id)
    
    def get_all_schedules(self) -> List[Schedule]:
        """Get all schedules."""
        return list(self.schedules.values())
    
    def get_due_schedules(self) -> List[Schedule]:
        """Get schedules that are due for execution."""
        due_schedules = []
        current_time = datetime.utcnow()
        
        for schedule in self.schedules.values():
            if schedule.should_execute() and schedule.next_run:
                if current_time >= schedule.next_run:
                    due_schedules.append(schedule)
        
        return due_schedules
    
    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule."""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            schedule.pause()
            logger.info(f"Paused schedule {schedule_id}")
            return True
        return False
    
    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a schedule."""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            schedule.resume()
            logger.info(f"Resumed schedule {schedule_id}")
            return True
        return False
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        logger.info("Cron scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Cron scheduler stopped")
    
    def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while not self.stop_event.is_set():
            try:
                self._process_due_schedules()
                self._cleanup_completed_schedules()
                
                # Sleep for a short interval
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _process_due_schedules(self) -> None:
        """Process schedules that are due for execution."""
        due_schedules = self.get_due_schedules()
        
        for schedule in due_schedules:
            try:
                self._execute_schedule(schedule)
            except Exception as e:
                logger.error(f"Error executing schedule {schedule.id}: {e}")
                schedule.increment_retry_count()
                
                if not schedule.has_retries_left():
                    schedule.fail()
                    logger.error(f"Schedule {schedule.id} failed after max retries")
    
    def _execute_schedule(self, schedule: Schedule) -> None:
        """Execute a schedule."""
        logger.info(f"Executing schedule {schedule.id}: {schedule.name}")
        
        # This would typically create and execute commands from template
        # For now, we'll just update the schedule
        schedule.increment_execution_count()
        schedule.reset_retry_count()
        
        logger.info(f"Schedule {schedule.id} executed successfully")
    
    def _cleanup_completed_schedules(self) -> None:
        """Clean up completed or failed schedules."""
        to_remove = []
        
        for schedule_id, schedule in self.schedules.items():
            if schedule.status in [ScheduleStatus.COMPLETED, ScheduleStatus.FAILED]:
                to_remove.append(schedule_id)
            elif schedule.max_executions and schedule.execution_count >= schedule.max_executions:
                schedule.complete()
                to_remove.append(schedule_id)
        
        for schedule_id in to_remove:
            self.remove_schedule(schedule_id)
    
    def get_scheduler_stats(self) -> Dict[str, any]:
        """Get scheduler statistics."""
        active_schedules = [s for s in self.schedules.values() if s.is_active()]
        paused_schedules = [s for s in self.schedules.values() if s.status == ScheduleStatus.PAUSED]
        
        return {
            "running": self.running,
            "total_schedules": len(self.schedules),
            "active_schedules": len(active_schedules),
            "paused_schedules": len(paused_schedules),
            "next_execution": min(
                (s.next_run for s in active_schedules if s.next_run),
                default=None
            ),
        }
    
    def __del__(self) -> None:
        """Cleanup on object destruction."""
        self.stop() 