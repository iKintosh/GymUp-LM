"""CLI interface for GymUp Tracker."""

import subprocess
import sys
import webbrowser
from pathlib import Path
from time import sleep

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GymUp AI Trainer - Workout Analysis & AI Recommendations"""
    pass


@cli.command()
@click.option(
    "--db",
    type=click.Path(exists=True, path_type=Path),
    help="Path to GymUp database file",
)
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Port to run the server on",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't automatically open browser",
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="Skip AI setup (Ollama)",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="Ollama model to use (default: mistral:7b)",
)
def start(db: Path, port: int, no_browser: bool, no_ai: bool, model: str):
    """Start the GymUp Tracker web interface."""
    console.print(Panel.fit(
        "[bold blue]GymUp AI Trainer[/bold blue]\n"
        "Workout Analysis & AI Recommendations",
        border_style="blue",
    ))

    # Find database if not provided
    if not db:
        candidates = [
            Path.cwd() / "workout.db",
            Path.cwd() / "data" / "workout.db",
        ]

        # Check for any .db file
        for db_file in Path.cwd().glob("*.db"):
            candidates.insert(0, db_file)

        for candidate in candidates:
            if candidate.exists():
                db = candidate
                break

    if db:
        console.print(f"[green]OK[/green] Database: {db}")
    else:
        console.print("[yellow]!![/yellow] No database specified. Upload one in the UI.")

    # Setup AI (Ollama)
    if not no_ai:
        try:
            from gymup_tracker.llm.setup import ensure_ollama_ready
            ensure_ollama_ready(model=model, auto_install=True)
        except Exception as e:
            console.print(f"[yellow]!![/yellow] AI setup issue: {e}")
            console.print("    Continuing without AI features. Use --no-ai to skip this check.")
    else:
        console.print("[dim]AI features disabled (--no-ai)[/dim]")

    # Build streamlit command
    app_path = Path(__file__).parent / "ui" / "app.py"

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]

    if db:
        cmd.extend(["--", f"--db={db}"])

    console.print(f"\n[bold]Starting server on port {port}...[/bold]")

    url = f"http://localhost:{port}"
    if db:
        url += f"?db={db}"

    console.print(f"[blue]→[/blue] {url}\n")

    # Open browser after short delay
    if not no_browser:
        def open_browser():
            sleep(2)
            webbrowser.open(url)

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

    # Run streamlit
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting server: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--db",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to GymUp database file",
)
def info(db: Path):
    """Show database information and statistics."""
    console.print(Panel.fit(
        f"[bold]Database Info[/bold]\n{db}",
        border_style="blue",
    ))

    try:
        from gymup_tracker.db import QueryService

        query = QueryService(db)
        stats = query.get_overview_stats()

        # Overview table
        table = Table(title="Overview Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Workouts", str(stats["total_trainings"]))
        table.add_row("Total Volume", f"{stats['total_tonnage']:,.0f} kg")
        table.add_row("Total Sets", str(stats["total_sets"]))
        table.add_row("Total Reps", str(stats["total_reps"]))
        table.add_row("This Week", f"{stats['week_trainings']} workouts, {stats['week_tonnage']:,.0f} kg")
        table.add_row("This Month", f"{stats['month_trainings']} workouts, {stats['month_tonnage']:,.0f} kg")

        console.print(table)

        # Programs
        programs = query.get_all_programs()

        if programs:
            console.print(f"\n[bold]Programs ({len(programs)}):[/bold]")
            for p in programs[:10]:
                console.print(f"  • {p.name}")
            if len(programs) > 10:
                console.print(f"  ... and {len(programs) - 10} more")

        # Recent exercises
        from gymup_tracker.db.constants import get_exercise_display_name
        exercises = query.get_used_exercises()

        if exercises:
            console.print(f"\n[bold]Exercises Used ({len(exercises)}):[/bold]")
            for ex in exercises[:10]:
                stats = query.get_exercise_stats(ex.id)
                sessions = stats.get("total_sessions", 0)
                name = get_exercise_display_name(ex)
                console.print(f"  • {name} ({sessions} sessions)")

            if len(exercises) > 10:
                console.print(f"  ... and {len(exercises) - 10} more")

    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--install",
    is_flag=True,
    help="Automatically install and setup Ollama",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="Model to install (default: mistral:7b)",
)
def setup_ollama(install: bool, model: str):
    """Check Ollama status and optionally install/setup."""
    console.print(Panel.fit(
        "[bold]Ollama Setup[/bold]",
        border_style="blue",
    ))

    try:
        from gymup_tracker.llm.setup import (
            is_ollama_installed,
            ensure_ollama_ready,
            get_recommended_models,
        )
        from gymup_tracker.llm.client import get_ollama_status

        if install:
            # Full automatic setup
            success = ensure_ollama_ready(model=model, auto_install=True)
            if success:
                console.print("\n[bold green]Setup complete! AI features are ready.[/bold green]")
            else:
                console.print("\n[yellow]Setup incomplete. Some features may not work.[/yellow]")
            return

        # Just show status
        if not is_ollama_installed():
            console.print("[red]X[/red] Ollama is not installed")
            console.print("\nRun with --install to automatically install:")
            console.print("  [cyan]gymup-tracker setup-ollama --install[/cyan]")
            return

        console.print("[green]OK[/green] Ollama is installed")

        status = get_ollama_status()

        if status["available"]:
            console.print("[green]OK[/green] Ollama server is running")
            console.print(f"    URL: {status['base_url']}")

            if status["models"]:
                console.print("\n[bold]Available Models:[/bold]")
                for m in status["models"]:
                    marker = "[green]OK[/green]" if m == status["configured_model"] else "  "
                    console.print(f"  {marker} {m}")
            else:
                console.print("\n[yellow]No models installed.[/yellow]")

            if not status["model_ready"]:
                console.print(f"\n[yellow]Default model not available:[/yellow] {status['configured_model']}")
                console.print("\nRun to install:")
                console.print(f"  [cyan]gymup-tracker setup-ollama --install --model {status['configured_model']}[/cyan]")
        else:
            console.print("[yellow]!![/yellow] Ollama server is not running")
            console.print("\nRun with --install to start automatically:")
            console.print("  [cyan]gymup-tracker setup-ollama --install[/cyan]")

        # Show recommended models
        console.print("\n[bold]Recommended Models:[/bold]")
        for rec in get_recommended_models():
            rec_marker = " (recommended)" if rec["recommended"] else ""
            console.print(f"  • {rec['name']}: {rec['description']}{rec_marker}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option(
    "--db",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to GymUp database file",
)
@click.argument("exercise_name")
def analyze(db: Path, exercise_name: str):
    """Analyze progression for a specific exercise."""
    console.print(Panel.fit(
        f"[bold]Analyzing: {exercise_name}[/bold]",
        border_style="blue",
    ))

    try:
        from gymup_tracker.db import QueryService
        from gymup_tracker.db.constants import get_muscle_name, get_equipment_name, get_exercise_display_name
        from gymup_tracker.analytics.progression import analyze_progression

        query = QueryService(db)

        # Find exercise
        exercises = query.get_used_exercises()
        matching = [
            e for e in exercises
            if e.name and exercise_name.lower() in e.name.lower()
        ]

        if not matching:
            console.print(f"[red]No exercise found matching '{exercise_name}'[/red]")
            console.print("\nAvailable exercises:")
            for ex in exercises[:10]:
                console.print(f"  • {get_exercise_display_name(ex)}")
            return

        exercise = matching[0]
        name = get_exercise_display_name(exercise)
        console.print(f"\nFound: [green]{name}[/green]")
        console.print(f"Muscle: {get_muscle_name(exercise.mainMuscleWorked)}")
        console.print(f"Equipment: {get_equipment_name(exercise.equipment)}")

        # Get history and analyze
        history = query.get_exercise_history(exercise.id, weeks=12)

        if not history:
            console.print("\n[yellow]No workout history found.[/yellow]")
            return

        analysis = analyze_progression(history)

        # Display results
        console.print(f"\n[bold]Analysis (last {analysis.weeks_analyzed} weeks):[/bold]")

        trend_colors = {
            "improving": "green",
            "plateau": "yellow",
            "declining": "red",
            "stable": "blue",
        }
        color = trend_colors.get(analysis.trend, "white")
        console.print(f"  Trend: [{color}]{analysis.trend.upper()}[/{color}]")
        console.print(f"  Weight change: {analysis.weight_change:+.1f} kg ({analysis.weight_change_percent:+.1f}%)")
        console.print(f"  Est. 1RM: {analysis.estimated_1rm:.1f} kg")
        console.print(f"  Personal records: {analysis.pr_count}")

        if analysis.plateau_weeks > 0:
            console.print(f"  [yellow]Plateau: {analysis.plateau_weeks} weeks[/yellow]")

        console.print(f"\n[bold]Recommendation:[/bold]")
        console.print(f"  {analysis.recommendation}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
