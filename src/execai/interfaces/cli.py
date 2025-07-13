"""
CLI entry point for execAI.

This module provides the main entry point for the execai command
as defined in pyproject.toml.
"""

from .cli.main import app

if __name__ == "__main__":
    app() 