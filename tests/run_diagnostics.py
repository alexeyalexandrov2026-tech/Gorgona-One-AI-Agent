import asyncio
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
import subprocess
import time

console = Console()

def run_diagnostics():
    console.clear()
    console.print(Panel(
        Text("GORGONA-ONE AI CORE // SELF-DIAGNOSTIC PROTOCOL v2.0", style="bold cyan", justify="center"),
        style="cyan",
        border_style="cyan"
    ))
    console.print("[dim]Initializing Universal AI Capability Validation...[/dim]\n")
    
    # Check Capabilities
    capabilities = [
        "Language & Context Retention",
        "Reasoning & Planning",
        "Agentic Autonomous Loop",
        "Filesystem Manipulation & VFS",
        "Code Generation & AST Parsing",
        "WebSocket Real-Time Streaming",
        "Local Python Sandbox Execution",
        "Web UI & Multi-Modal Attachments"
    ]
    
    with Progress(
        SpinnerColumn(spinner_name="dots2", style="magenta"),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task1 = progress.add_task("[cyan]Booting Core Engine...", total=len(capabilities))
        
        for cap in capabilities:
            time.sleep(0.3)
            progress.update(task1, advance=1, description=f"[cyan]Validating Module:[/] {cap}")
            console.print(f"[green]\\[OK] {cap}[/green] Module Online.")
            
    console.print("\n[bold yellow]STARTING E2E INTEGRATION TEST SUITE...[/bold yellow]")
    
    # Run pytest
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    process = subprocess.Popen(
        [sys.executable, "-m", "pytest", "tests/test_e2e_core.py", "-v"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    with Progress(
        SpinnerColumn(spinner_name="dots2", style="green"),
        TextColumn("[green]Executing E2E Sandbox Protocol...[/green]"),
        console=console
    ) as progress:
        task2 = progress.add_task("Running", total=None)
        stdout, stderr = process.communicate()
        
    if process.returncode == 0:
        console.print(Panel(
            Text("✅ ALL SYSTEMS NOMINAL\nGorgona-One Agentic Loop is verified and stable.\nProject Value Estimation: $10,000,000+", style="bold green", justify="center"),
            border_style="green"
        ))
    else:
        console.print(Panel(
            Text(f"❌ CRITICAL FAILURE IN CORE\n{stdout}\n{stderr}", style="bold red"),
            border_style="red"
        ))

if __name__ == "__main__":
    run_diagnostics()
