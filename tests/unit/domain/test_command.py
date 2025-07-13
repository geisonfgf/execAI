"""
Unit tests for the Command entity.

This module contains unit tests for the Command domain entity
including validation, state transitions, and business logic.
"""

import pytest

from execai.domain.entities.command import Command, CommandStatus, CommandType


class TestCommand:
    """Test cases for the Command entity."""
    
    def test_command_creation(self):
        """Test basic command creation."""
        command = Command(
            original_request="list files",
            parsed_command="ls -la"
        )
        
        assert command.original_request == "list files"
        assert command.parsed_command == "ls -la"
        assert command.status == CommandStatus.PENDING
        assert command.command_type == CommandType.SYSTEM
        assert command.requires_confirmation is True
        assert command.safe_mode is True
        assert command.timeout == 300
    
    def test_command_validation(self):
        """Test command validation."""
        # Test empty parsed command
        with pytest.raises(ValueError, match="Parsed command cannot be empty"):
            Command(
                original_request="test",
                parsed_command=""
            )
        
        # Test invalid timeout
        with pytest.raises(ValueError, match="Timeout must be positive"):
            Command(
                original_request="test",
                parsed_command="ls",
                timeout=0
            )
    
    def test_safe_command_detection(self):
        """Test safe command detection."""
        # Safe command
        safe_command = Command(
            original_request="list files",
            parsed_command="ls -la"
        )
        assert safe_command.is_safe_command() is True
        
        # Dangerous command
        dangerous_command = Command(
            original_request="delete files",
            parsed_command="rm -rf /"
        )
        assert dangerous_command.is_safe_command() is False
    
    def test_command_execution_flow(self):
        """Test command execution state transitions."""
        command = Command(
            original_request="test",
            parsed_command="echo hello"
        )
        
        # Initial state
        assert command.status == CommandStatus.PENDING
        assert command.can_execute() is True
        
        # Start execution
        command.start_execution()
        assert command.status == CommandStatus.RUNNING
        assert command.executed_at is not None
        assert command.can_execute() is False
        
        # Complete execution
        command.complete_execution(0, "hello\n", "", 0.5)
        assert command.status == CommandStatus.COMPLETED
        assert command.exit_code == 0
        assert command.stdout == "hello\n"
        assert command.stderr == ""
        assert command.execution_time == 0.5
        assert command.completed_at is not None
    
    def test_command_failure(self):
        """Test command failure handling."""
        command = Command(
            original_request="test",
            parsed_command="invalid_command"
        )
        
        command.start_execution()
        command.complete_execution(1, "", "command not found", 0.1)
        
        assert command.status == CommandStatus.FAILED
        assert command.exit_code == 1
        assert command.stderr == "command not found"
    
    def test_command_cancellation(self):
        """Test command cancellation."""
        command = Command(
            original_request="test",
            parsed_command="sleep 10"
        )
        
        command.start_execution()
        command.cancel_execution()
        
        assert command.status == CommandStatus.CANCELLED
    
    def test_command_safe_mode(self):
        """Test safe mode restrictions."""
        dangerous_command = Command(
            original_request="delete files",
            parsed_command="rm -rf /",
            safe_mode=True
        )
        
        assert dangerous_command.can_execute() is False
        
        # Should work with safe mode disabled
        dangerous_command.safe_mode = False
        assert dangerous_command.can_execute() is True
    
    def test_command_string_representation(self):
        """Test string representations."""
        command = Command(
            original_request="test",
            parsed_command="ls"
        )
        
        str_repr = str(command)
        assert "Command" in str_repr
        assert "ls" in str_repr
        assert "PENDING" in str_repr
        
        detailed_repr = repr(command)
        assert "Command" in detailed_repr
        assert "test" in detailed_repr
        assert "ls" in detailed_repr 