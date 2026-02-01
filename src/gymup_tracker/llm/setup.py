"""Automatic Ollama setup and model management."""

import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from gymup_tracker.llm.client import OllamaClient, get_ollama_status
from gymup_tracker.config import settings

console = Console()


def is_ollama_installed() -> bool:
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ollama() -> bool:
    """Install Ollama (macOS/Linux only)."""
    console.print("[bold]Installing Ollama...[/bold]")

    if sys.platform == "darwin":
        # macOS - try brew first, then curl
        try:
            result = subprocess.run(
                ["brew", "install", "ollama"],
                capture_output=True,
                timeout=300,
            )
            if result.returncode == 0:
                console.print("[green]Ollama installed via Homebrew[/green]")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Fallback to curl installer
        console.print("Homebrew not available, using direct installer...")

    elif sys.platform.startswith("linux"):
        pass  # Will use curl installer below
    else:
        console.print("[red]Automatic installation not supported on this platform.[/red]")
        console.print("Please install Ollama manually from https://ollama.com/download")
        return False

    # Use curl installer for macOS (fallback) and Linux
    try:
        console.print("Downloading and installing Ollama...")
        result = subprocess.run(
            ["curl", "-fsSL", "https://ollama.com/install.sh"],
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0:
            # Pipe to sh
            install_result = subprocess.run(
                ["sh"],
                input=result.stdout,
                capture_output=True,
                timeout=300,
            )
            if install_result.returncode == 0:
                console.print("[green]Ollama installed successfully[/green]")
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        console.print(f"[red]Installation failed: {e}[/red]")

    console.print("[red]Could not install Ollama automatically.[/red]")
    console.print("Please install manually from https://ollama.com/download")
    return False


def start_ollama_server() -> bool:
    """Start the Ollama server if not running."""
    status = get_ollama_status()
    if status["available"]:
        return True

    console.print("[bold]Starting Ollama server...[/bold]")

    try:
        # Start ollama serve in background
        if sys.platform == "darwin":
            # On macOS, use 'open' to start as a background service
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:
            # Linux/other - start in background
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        # Wait for server to start
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Waiting for Ollama server...", total=None)

            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                status = get_ollama_status()
                if status["available"]:
                    progress.update(task, description="Ollama server started!")
                    console.print("[green]Ollama server is running[/green]")
                    return True

        console.print("[yellow]Ollama server did not start in time[/yellow]")
        return False

    except Exception as e:
        console.print(f"[red]Failed to start Ollama: {e}[/red]")
        return False


def pull_model(model: str = None) -> bool:
    """Pull/download a model if not available."""
    model = model or settings.llm.model

    client = OllamaClient()

    # Check if model already exists
    if client.has_model(model):
        console.print(f"[green]Model '{model}' is already available[/green]")
        return True

    console.print(f"[bold]Downloading model '{model}'...[/bold]")
    console.print("[dim]This may take a few minutes depending on your connection[/dim]")

    try:
        # Run ollama pull with real-time output
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Stream output
        for line in process.stdout:
            line = line.strip()
            if line:
                # Filter and format progress output
                if "pulling" in line.lower() or "%" in line:
                    console.print(f"  {line}", end="\r")
                elif "success" in line.lower():
                    console.print(f"\n[green]{line}[/green]")
                else:
                    console.print(f"  {line}")

        process.wait()

        if process.returncode == 0:
            console.print(f"[green]Model '{model}' downloaded successfully[/green]")
            return True
        else:
            console.print(f"[red]Failed to download model '{model}'[/red]")
            return False

    except FileNotFoundError:
        console.print("[red]Ollama command not found. Is Ollama installed?[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error downloading model: {e}[/red]")
        return False


def ensure_ollama_ready(model: str = None, auto_install: bool = True) -> bool:
    """
    Ensure Ollama is installed, running, and has the required model.

    Args:
        model: Model to ensure is available (defaults to settings)
        auto_install: Whether to automatically install Ollama if missing

    Returns:
        True if Ollama is ready with the model, False otherwise
    """
    model = model or settings.llm.model

    console.print("\n[bold blue]Checking AI Setup...[/bold blue]")

    # Step 1: Check if Ollama is installed
    if not is_ollama_installed():
        console.print("[yellow]Ollama is not installed[/yellow]")
        if auto_install:
            if not install_ollama():
                return False
        else:
            console.print("Please install Ollama from https://ollama.com/download")
            return False

    console.print("[green]Ollama is installed[/green]")

    # Step 2: Start server if not running
    if not start_ollama_server():
        console.print("[yellow]Could not start Ollama server[/yellow]")
        console.print("Try running 'ollama serve' manually in another terminal")
        return False

    # Step 3: Pull model if needed
    if not pull_model(model):
        console.print(f"[yellow]Could not download model '{model}'[/yellow]")
        console.print(f"Try running 'ollama pull {model}' manually")
        return False

    console.print(f"\n[bold green]AI Ready: {model}[/bold green]\n")
    return True


def get_recommended_models() -> list[dict]:
    """Get list of recommended models for this app."""
    return [
        {
            "name": "mistral:7b",
            "description": "Fast, good quality (4.1GB)",
            "recommended": True,
        },
        {
            "name": "llama3.2:3b",
            "description": "Very fast, smaller model (2GB)",
            "recommended": False,
        },
        {
            "name": "llama3.1:8b",
            "description": "High quality, slower (4.7GB)",
            "recommended": False,
        },
        {
            "name": "gemma2:9b",
            "description": "Google's model, good reasoning (5.4GB)",
            "recommended": False,
        },
    ]
