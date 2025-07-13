"""
Configuration settings for the execAI application.

This module defines the configuration settings using Pydantic Settings
for managing environment variables and application configuration.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    # Application
    app_name: str = Field(default="execAI", description="App name")
    app_version: str = Field(default="0.1.0", description="App version")
    app_environment: str = Field(default="development", description="Environment")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="test-key", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="Model")
    openai_temperature: float = Field(default=0.1, description="Temperature")
    openai_max_tokens: int = Field(default=2000, description="Max tokens")
    
    # LangChain Configuration
    langchain_tracing_v2: bool = Field(
        default=False, description="LangChain tracing"
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com", 
        description="LangChain endpoint"
    )
    langchain_api_key: Optional[str] = Field(
        None, description="LangChain API key"
    )
    langchain_project: str = Field(
        default="execai", description="LangChain project"
    )
    
    # Security
    secret_key: str = Field(
        default="test-secret-key", description="Secret key for encryption"
    )
    encryption_key: str = Field(
        default="test-encryption-key", description="Encryption key"
    )
    
    # Storage
    data_dir: str = Field(default="./data", description="Data directory")
    log_dir: str = Field(default="./logs", description="Log directory")
    cache_dir: str = Field(default="./cache", description="Cache directory")
    
    # Command Execution
    max_execution_time: int = Field(default=300, description="Max execution time")
    confirmation_required: bool = Field(default=True, description="Confirmation required")
    safe_mode: bool = Field(default=True, description="Safe mode enabled")
    allowed_commands: List[str] = Field(
        default_factory=lambda: ["ls", "pwd", "echo", "date", "whoami", "uname"],
        description="Allowed commands in safe mode"
    )
    
    # Scheduling
    scheduler_enabled: bool = Field(default=True, description="Scheduler enabled")
    max_concurrent_jobs: int = Field(default=5, description="Max concurrent jobs")
    default_timezone: str = Field(default="UTC", description="Default timezone")
    
    # Monitoring
    enable_telemetry: bool = Field(default=False, description="Enable telemetry")
    metrics_endpoint: str = Field(
        default="http://localhost:8080/metrics", description="Metrics endpoint"
    )
    
    # API Configuration
    api_host: str = Field(default="localhost", description="API host")
    api_port: int = Field(default=8000, description="API port")

    def is_development(self) -> bool:
        """Check if in development environment."""
        return self.app_environment.lower() == "development"
    
    def is_production(self) -> bool:
        """Check if in production environment."""
        return self.app_environment.lower() == "production"
    
    def is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute."""
        if not self.safe_mode:
            return True
        
        command_parts = command.split()
        if not command_parts:
            return False
        
        base_command = command_parts[0].lower()
        return base_command in self.allowed_commands


# Global settings instance
settings = Settings() 