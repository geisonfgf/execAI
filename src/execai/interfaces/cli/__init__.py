"""
CLI interface package for execAI.

This package provides the command-line interface implementation
using Typer and Rich for user interaction.
"""

from .main import app, cli_main

__all__ = ["app", "cli_main"] 