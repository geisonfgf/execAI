"""
Command Executor - Execute system commands safely and securely.

This module provides a secure command execution service with timeout
handling, resource monitoring, and safety checks.
"""

import subprocess
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import psutil
import os

from ...domain.entities.command import Command
from ...domain.entities.execution_result import ExecutionResult
from ...application.config import settings


class CommandExecutor:
    """
    Secure command executor with monitoring and safety features.
    
    This class provides safe command execution with timeout handling,
    resource monitoring, and comprehensive logging.
    """
    
    def __init__(self) -> None:
        """Initialize the command executor."""
        self.running_processes: Dict[str, subprocess.Popen] = {}
    
    async def execute_command(self, command: Command) -> ExecutionResult:
        """
        Execute a command and return the execution result.
        
        Args:
            command: The command to execute
            
        Returns:
            ExecutionResult: The result of the command execution
        """
        if not command.can_execute():
            raise ValueError(f"Command {command.id} cannot be executed")
        
        # Mark command as running
        command.start_execution()
        
        # Create execution result
        result = ExecutionResult(
            command_id=command.id,
            schedule_id=command.schedule_id,
            started_at=datetime.utcnow(),
            working_directory=command.working_directory,
            environment=command.environment_variables,
        )
        
        try:
            # Execute the command
            success, exit_code, stdout, stderr, execution_time = await self._run_command(
                command.parsed_command,
                command.timeout,
                command.working_directory,
                command.environment_variables,
            )
            
            # Update result
            result.success = success
            result.exit_code = exit_code
            result.stdout = stdout
            result.stderr = stderr
            result.execution_time = execution_time
            result.completed_at = datetime.utcnow()
            
            # Calculate duration
            result.duration = result.calculate_duration()
            
            # Update command
            command.complete_execution(exit_code, stdout, stderr, execution_time)
            
        except Exception as e:
            # Handle execution error
            result.success = False
            result.stderr = str(e)
            result.completed_at = datetime.utcnow()
            result.duration = result.calculate_duration()
            
            # Update command
            command.complete_execution(1, "", str(e), 0.0)
        
        return result
    
    async def _run_command(
        self,
        command: str,
        timeout: int,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, int, str, str, float]:
        """
        Run a command with timeout and monitoring.
        
        Args:
            command: The command to execute
            timeout: Timeout in seconds
            working_directory: Working directory for execution
            environment: Environment variables
            
        Returns:
            Tuple of (success, exit_code, stdout, stderr, execution_time)
        """
        start_time = time.time()
        
        # Prepare environment
        env = os.environ.copy()
        if environment:
            env.update(environment)
        
        # Prepare command
        cmd_parts = command.split()
        
        try:
            # Create process
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_directory,
                env=env,
                preexec_fn=os.setsid,  # Create process group for clean termination
            )
            
            # Store process for potential cancellation
            process_id = str(id(process))
            self.running_processes[process_id] = process
            
            try:
                # Wait for process with timeout
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                
                execution_time = time.time() - start_time
                success = exit_code == 0
                
                return success, exit_code, stdout, stderr, execution_time
                
            except subprocess.TimeoutExpired:
                # Handle timeout
                self._terminate_process(process)
                execution_time = time.time() - start_time
                
                return False, -1, "", f"Command timed out after {timeout} seconds", execution_time
                
            finally:
                # Clean up
                self.running_processes.pop(process_id, None)
                
        except Exception as e:
            execution_time = time.time() - start_time
            return False, -1, "", str(e), execution_time
    
    def _terminate_process(self, process: subprocess.Popen) -> None:
        """Terminate a process gracefully."""
        try:
            # Try graceful termination first
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                process.wait()
        except ProcessLookupError:
            # Process already terminated
            pass
    
    def cancel_command(self, command_id: str) -> bool:
        """
        Cancel a running command.
        
        Args:
            command_id: ID of the command to cancel
            
        Returns:
            True if command was cancelled, False otherwise
        """
        for process_id, process in self.running_processes.items():
            if process_id == command_id:
                self._terminate_process(process)
                return True
        return False
    
    def get_running_commands(self) -> Dict[str, Dict[str, any]]:
        """Get information about currently running commands."""
        running = {}
        for process_id, process in self.running_processes.items():
            try:
                psutil_process = psutil.Process(process.pid)
                running[process_id] = {
                    "pid": process.pid,
                    "status": psutil_process.status(),
                    "cpu_percent": psutil_process.cpu_percent(),
                    "memory_info": psutil_process.memory_info(),
                    "create_time": psutil_process.create_time(),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process no longer exists or access denied
                continue
        return running
    
    def cleanup(self) -> None:
        """Clean up any running processes."""
        for process in self.running_processes.values():
            self._terminate_process(process)
        self.running_processes.clear() 