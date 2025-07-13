"""
Main CLI interface for execAI.

This module provides the command-line interface for the execAI application
using Typer for natural language command processing and scheduling.
"""

import asyncio
import sys

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from ...application.agents.command_agent import CommandAgent
from ...application.config import settings
from ...infrastructure.scheduler.cron_scheduler import CronScheduler
from ...infrastructure.executor.command_executor import CommandExecutor

# Create the main Typer app
app = typer.Typer(
    name="execai",
    help="CLI AI Agent to run and schedule commands with natural language",
    add_completion=False
)

# Create console for rich output
console = Console()

# Global instances
agent = CommandAgent()
scheduler = CronScheduler()
executor = CommandExecutor()


@app.command()
def run(
    request: str = typer.Argument(..., help="Natural language command request"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    schedule: bool = typer.Option(False, "--schedule", "-s", help="Schedule command"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Show commands"),
) -> None:
    """
    Process a natural language request and execute commands.
    
    Examples:
        execai run "list all files in current directory"
        execai run "show system information" --force
        execai run "backup files every day at 2 AM" --schedule
    """
    console.print(f"[bold blue]Processing request:[/bold blue] {request}")
    
    try:
        # Process the request
        result = agent.process_request(request)
        
        # Check for errors
        if result["errors"]:
            console.print("[bold red]Errors occurred:[/bold red]")
            for error in result["errors"]:
                console.print(f"  • {error}")
            return
        
        # Display command summary
        summary = agent.get_command_summary(result)
        console.print(Panel(summary, title="Command Summary", border_style="green"))
        
        # Handle dry run
        if dry_run:
            console.print("[yellow]Dry run mode - no commands executed[/yellow]")
            return
        
        # Handle confirmation
        if result["requires_confirmation"] and not force:
            if not Confirm.ask("Do you want to proceed with execution?"):
                console.print("[yellow]Execution cancelled by user[/yellow]")
                return
        
        # Execute commands or schedule them
        if result["schedule"]:
            scheduler.add_schedule(result["schedule"])
            console.print("[green]Schedule added successfully[/green]")
        else:
            for command in result["commands"]:
                console.print(f"[blue]Executing:[/blue] {command.parsed_command}")
                execution_result = asyncio.run(executor.execute_command(command))
                
                if execution_result.is_successful():
                    console.print("[green]✓ Command executed successfully[/green]")
                    if execution_result.has_output():
                        console.print(execution_result.stdout)
                else:
                    console.print("[red]✗ Command execution failed[/red]")
                    if execution_result.has_errors():
                        console.print(f"Error: {execution_result.stderr}")
                
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if settings.debug:
            console.print_exception()


@app.command()
def schedules() -> None:
    """List all scheduled tasks."""
    schedules = scheduler.get_all_schedules()
    
    if not schedules:
        console.print("[yellow]No scheduled tasks found[/yellow]")
        return
    
    table = Table(title="Scheduled Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Next Run", style="blue")
    table.add_column("Executions", style="red")
    
    for schedule in schedules:
        table.add_row(
            str(schedule.id)[:8],
            schedule.name,
            schedule.schedule_type,
            schedule.status,
            schedule.next_run.strftime("%Y-%m-%d %H:%M:%S") if schedule.next_run else "N/A",
            f"{schedule.execution_count}/{schedule.max_executions or '∞'}"
        )
    
    console.print(table)


@app.command()
def pause(
    schedule_id: str = typer.Argument(..., help="Schedule ID to pause")
) -> None:
    """Pause a scheduled task."""
    if scheduler.pause_schedule(schedule_id):
        console.print(f"[green]Schedule {schedule_id} paused[/green]")
    else:
        console.print(f"[red]Schedule {schedule_id} not found[/red]")


@app.command()
def resume(
    schedule_id: str = typer.Argument(..., help="Schedule ID to resume")
) -> None:
    """Resume a paused scheduled task."""
    if scheduler.resume_schedule(schedule_id):
        console.print(f"[green]Schedule {schedule_id} resumed[/green]")
    else:
        console.print(f"[red]Schedule {schedule_id} not found[/red]")


@app.command()
def cancel(
    schedule_id: str = typer.Argument(..., help="Schedule ID to cancel")
) -> None:
    """Cancel a scheduled task."""
    if scheduler.remove_schedule(schedule_id):
        console.print(f"[green]Schedule {schedule_id} cancelled[/green]")
    else:
        console.print(f"[red]Schedule {schedule_id} not found[/red]")


@app.command()
def status() -> None:
    """Show system status and statistics."""
    stats = scheduler.get_scheduler_stats()
    running_commands = executor.get_running_commands()
    
    # Create status table
    table = Table(title="System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    table.add_row("Scheduler", "Running" if stats["running"] else "Stopped", f"{stats['active_schedules']} active schedules")
    table.add_row("Executor", "Ready", f"{len(running_commands)} running commands")
    table.add_row("Safe Mode", "Enabled" if settings.safe_mode else "Disabled", f"Allowed: {len(settings.allowed_commands)} commands")
    
    console.print(table)
    
    # Show next execution
    if stats["next_execution"]:
        console.print(f"[blue]Next execution:[/blue] {stats['next_execution']}")


@app.command()
def config() -> None:
    """Show current configuration."""
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Environment", settings.app_environment)
    config_table.add_row("Log Level", settings.log_level)
    config_table.add_row("Safe Mode", str(settings.safe_mode))
    config_table.add_row("Confirmation Required", str(settings.confirmation_required))
    config_table.add_row("Max Execution Time", f"{settings.max_execution_time}s")
    config_table.add_row("Scheduler Enabled", str(settings.scheduler_enabled))
    config_table.add_row("Max Concurrent Jobs", str(settings.max_concurrent_jobs))
    
    console.print(config_table)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"[bold blue]execAI[/bold blue] version {settings.app_version}")
    console.print(f"Environment: {settings.app_environment}")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
) -> None:
    """
    execAI - CLI AI Agent to run and schedule commands with natural language.
    
    This tool allows you to execute system commands and schedule tasks using
    natural language descriptions powered by AI.
    """
    if debug:
        settings.debug = True
    
    if verbose:
        settings.log_level = "DEBUG"
    
    # Start scheduler if enabled
    if settings.scheduler_enabled:
        scheduler.start()


def cli_main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {str(e)}")
        if settings.debug:
            console.print_exception()
        sys.exit(1)
    finally:
        # Cleanup
        scheduler.stop()
        executor.cleanup()


if __name__ == "__main__":
    cli_main() 