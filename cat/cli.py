"""CLI commands for Claude Agent Teams."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from rich.table import Table

from cat.data import TaskLoader, StatsLoader, TaskStatus

app = typer.Typer(
    name="catt",
    help="Claude Agent Teams - Interactive CLI with Kanban dashboard",
    no_args_is_help=True,
)
console = Console()


# =============================================================================
# Init Command
# =============================================================================


@app.command()
def init(
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-n", help="Run interactive wizard"),
    working_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Working directory"),
):
    """Initialize a new CATT project with interactive wizard."""
    from cat.interactive.wizard import run_wizard
    from cat.interactive.config import ProjectConfig

    work_dir = working_dir or Path.cwd()

    if interactive:
        config = run_wizard(work_dir)
        if not config:
            raise typer.Exit(1)
    else:
        # Non-interactive: create default config
        config = ProjectConfig(
            name=work_dir.name,
            description="",
            use_case="build_feature",
            working_dir=work_dir,
        )
        config.ensure_directories()
        config_path = config.save()
        console.print(f"[green]✓[/green] Default config saved to {config_path}")


# =============================================================================
# Run Command
# =============================================================================


@app.command()
def run(
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file path"),
    max_iterations: int = typer.Option(40, "--max-iterations", "-m", help="Max iterations per agent"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without executing"),
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume from saved state"),
):
    """Run the agent workflow from configuration."""
    from cat.interactive.config import ProjectConfig

    # Find or load config
    try:
        if config_file:
            if not config_file.exists():
                console.print(f"[red]Config file not found: {config_file}[/red]")
                raise typer.Exit(1)
            config = ProjectConfig.load(config_file)
        else:
            config = ProjectConfig.load_or_none()
            if not config:
                console.print("[yellow]No project configuration found.[/yellow]")
                console.print("Run [cyan]catt init[/cyan] to create one.")
                raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)

    # Show execution plan
    console.print()
    console.print(Panel(
        f"[bold]{config.name}[/bold]\n{config.description}",
        title="Project",
    ))

    workflow = config.agent_workflow_order
    console.print()
    console.print("[bold]Execution Plan:[/bold]")
    for i, agent in enumerate(workflow, 1):
        deps = f" [dim](after: {', '.join(agent.depends_on)})[/dim]" if agent.depends_on else ""
        console.print(f"  {i}. {agent.role.display_name} ({agent.model.value}){deps}")

    if dry_run:
        console.print()
        console.print("[yellow]Dry run - showing team prompt[/yellow]")
        console.print()
        team_prompt = config.generate_team_prompt()
        console.print(Panel(team_prompt, title="Team Creation Prompt"))
        return

    # Generate team prompt
    team_prompt = config.generate_team_prompt()

    # Save prompt to file for reference
    config.ensure_directories()
    prompt_file = config.config_dir / "team_prompt.md"
    with open(prompt_file, "w") as f:
        f.write(team_prompt)

    console.print()
    console.print("[yellow]Starting Claude Code Agent Team...[/yellow]")
    console.print()
    console.print("[bold]How it works:[/bold]")
    console.print("  1. Claude Code will create an agent team with your specified roles")
    console.print("  2. Teammates will coordinate using the built-in task list")
    console.print("  3. Use Shift+Up/Down to switch between teammates")
    console.print("  4. Press Ctrl+T to view the shared task list")
    console.print()
    console.print(f"[dim]Team prompt saved to: {prompt_file}[/dim]")
    console.print()

    # Check for Claude Code
    import shutil
    import subprocess
    import os

    if not shutil.which("claude"):
        console.print("[red]Error: Claude Code CLI not found[/red]")
        console.print("Install from: [cyan]https://claude.ai/code[/cyan]")
        raise typer.Exit(1)

    # Launch Claude Code with the team prompt
    console.print("[green]Launching Claude Code with agent team...[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    try:
        # Change to working directory and launch claude
        os.chdir(config.working_dir)
        subprocess.run(
            ["claude", team_prompt],
            check=True
        )
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Claude Code exited with error: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")


# =============================================================================
# Agent Subcommands
# =============================================================================


agent_app = typer.Typer(help="Agent management commands")
app.add_typer(agent_app, name="agent")


@agent_app.command("list")
def agent_list():
    """List all agents and their status."""
    import json
    from cat.interactive.config import ProjectConfig

    config = ProjectConfig.load_or_none()
    if not config:
        console.print("[yellow]No project configuration found.[/yellow]")
        return

    # Try to load runtime state
    state_file = config.config_dir / "state.json"
    runtime_state = {}
    if state_file.exists():
        try:
            with open(state_file) as f:
                data = json.load(f)
                runtime_state = data.get("agents", {})
        except (json.JSONDecodeError, OSError):
            pass

    table = Table(title="Agents", show_header=True)
    table.add_column("Role", style="cyan")
    table.add_column("Model")
    table.add_column("Status")
    table.add_column("Enabled")
    table.add_column("Dependencies")

    status_styles = {
        "idle": "[dim]idle[/dim]",
        "starting": "[yellow]starting[/yellow]",
        "running": "[blue]running[/blue]",
        "waiting": "[yellow]waiting[/yellow]",
        "completed": "[green]completed[/green]",
        "failed": "[red]failed[/red]",
    }

    for role, agent_config in config.agents.items():
        # Get actual status from state file if available
        agent_state = runtime_state.get(role, {})
        status_value = agent_state.get("status", "idle")
        status = status_styles.get(status_value, f"[dim]{status_value}[/dim]")
        enabled = "[green]✓[/green]" if agent_config.enabled else "[dim]✗[/dim]"
        deps = ", ".join(agent_config.depends_on) if agent_config.depends_on else "-"

        table.add_row(
            agent_config.role.display_name,
            agent_config.model.value,
            status,
            enabled,
            deps,
        )

    console.print()
    console.print(table)
    console.print()


@agent_app.command("status")
def agent_status(
    role: str = typer.Argument(..., help="Agent role (e.g., 'researcher', 'developer')"),
):
    """Show detailed status for a specific agent."""
    from cat.interactive.config import ProjectConfig
    from cat.agent.models import AgentRole

    config = ProjectConfig.load_or_none()
    if not config:
        console.print("[yellow]No project configuration found.[/yellow]")
        return

    # Validate role
    try:
        agent_role = AgentRole(role.lower())
    except ValueError:
        console.print(f"[red]Unknown role: {role}[/red]")
        console.print(f"Valid roles: {', '.join(r.value for r in AgentRole)}")
        raise typer.Exit(1)

    if agent_role.value not in config.agents:
        console.print(f"[red]Agent '{role}' not configured[/red]")
        raise typer.Exit(1)

    agent_config = config.agents[agent_role.value]

    # Show agent details
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold")
    info.add_column()
    info.add_row("Role:", agent_config.role.display_name)
    info.add_row("Model:", agent_config.model.value)
    info.add_row("Enabled:", "Yes" if agent_config.enabled else "No")
    info.add_row("Max Iterations:", str(agent_config.max_iterations))
    info.add_row("Dependencies:", ", ".join(agent_config.depends_on) or "None")

    console.print()
    console.print(Panel(info, title=f"[bold]Agent: {agent_config.role.display_name}[/bold]"))
    console.print()


@agent_app.command("logs")
def agent_logs(
    role: str = typer.Argument(..., help="Agent role"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
):
    """Show recent output from an agent."""
    from cat.interactive.config import ProjectConfig
    from cat.agent.models import AgentRole

    config = ProjectConfig.load_or_none()
    if not config:
        console.print("[yellow]No project configuration found.[/yellow]")
        return

    # Validate role
    try:
        agent_role = AgentRole(role.lower())
    except ValueError:
        console.print(f"[red]Unknown role: {role}[/red]")
        raise typer.Exit(1)

    # Check for log file
    log_file = config.config_dir / "logs" / f"{agent_role.value}.log"
    if not log_file.exists():
        console.print(f"[yellow]No logs found for {agent_role.display_name}[/yellow]")
        return

    # Show last N lines
    content = log_file.read_text()
    log_lines = content.strip().split("\n")
    recent = log_lines[-lines:]

    console.print(f"\n[bold]Logs: {agent_role.display_name}[/bold] (last {len(recent)} lines)\n")
    for line in recent:
        console.print(line)
    console.print()


# =============================================================================
# Chat Command
# =============================================================================


@app.command()
def chat(
    agent: str = typer.Argument(..., help="Agent role to chat with"),
):
    """Open interactive chat with a specific agent."""
    from cat.interactive.config import ProjectConfig
    from cat.agent.models import AgentRole

    config = ProjectConfig.load_or_none()
    if not config:
        console.print("[yellow]No project configuration found.[/yellow]")
        console.print("Run [cyan]catt init[/cyan] first.")
        raise typer.Exit(1)

    # Validate role
    try:
        agent_role = AgentRole(agent.lower())
    except ValueError:
        console.print(f"[red]Unknown role: {agent}[/red]")
        console.print(f"Valid roles: {', '.join(r.value for r in AgentRole)}")
        raise typer.Exit(1)

    console.print(f"\n[bold]Chat with {agent_role.display_name}[/bold]")
    console.print("[dim]Type 'quit' or Ctrl+C to exit[/dim]\n")

    # TODO: Implement actual chat via tmux send-keys
    try:
        while True:
            message = console.input("[cyan]You:[/cyan] ")
            if message.lower() in ("quit", "exit", "q"):
                break
            console.print(f"[dim]Message queued for {agent_role.display_name}[/dim]")
            console.print("[yellow]Chat functionality requires running workflow[/yellow]")
    except KeyboardInterrupt:
        pass

    console.print("\n[dim]Chat ended[/dim]")


# =============================================================================
# Dashboard Command
# =============================================================================


@app.command()
def dashboard(
    watch: bool = typer.Option(False, "--watch", "-w", help="Auto-refresh on file changes"),
    multi_agent: bool = typer.Option(False, "--multi-agent", "-m", help="Show multi-agent view"),
):
    """Launch the Kanban TUI dashboard."""
    from cat.dashboard.app import DashboardApp

    dash_app = DashboardApp(watch=watch)
    dash_app.run()


@app.command()
def tmux(
    session: str = typer.Option("catt-agents", "--session", "-s", help="Tmux session name"),
):
    """Launch interactive Tmux Agent Manager.

    Provides a beautiful CLI UI to manage tmux agent sessions without knowing tmux commands.

    Features:
    - View all active agents
    - See live output from each agent
    - Send commands to agents
    - Switch between agents with arrow keys
    - Kill agents with Ctrl+K
    - Attach to tmux with 'a' key

    Keyboard Shortcuts:
    - ↑/↓: Navigate agents
    - Enter: Select agent
    - Type & Enter: Send command to agent
    - r: Refresh
    - a: Attach to tmux session
    - Ctrl+K: Kill current agent
    - Ctrl+L: Clear output
    - q: Quit
    """
    from cat.dashboard.tmux_manager import run_tmux_manager

    console.print()
    console.print("[bold cyan]🚀 Launching Tmux Agent Manager...[/bold cyan]")
    console.print(f"[dim]Session: {session}[/dim]")
    console.print()

    try:
        run_tmux_manager(session_name=session)
    except KeyboardInterrupt:
        console.print("\n[yellow]Manager closed.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@app.command()
def monitor(
    session: str = typer.Option("catt-agents", "--session", "-s", help="Tmux session name"),
):
    """Launch Unified Agent & Task Monitor.

    Combines tmux agent monitoring with kanban task board in a single unified interface.

    Features:
    - 🤖 View all active agents (left panel)
    - 📺 Live agent output (center panel)
    - 📋 Kanban task board (right panel)
    - 📊 Real-time statistics (bottom panel)
    - ⌨️ Keyboard navigation
    - 🔄 Auto-refresh every 2-5 seconds

    Keyboard Shortcuts:
    - ↑/↓: Navigate between agents
    - r: Refresh all panels
    - Ctrl+K: Kill selected agent
    - a: Attach to tmux session
    - q: Quit

    This is the all-in-one monitoring solution that combines:
    - Agent management (from catt tmux)
    - Task tracking (from catt tasks --kanban)
    - Statistics dashboard
    """
    from cat.dashboard.unified_manager import run_unified_manager

    console.print()
    console.print("[bold cyan]🚀 Launching Unified Monitor...[/bold cyan]")
    console.print(f"[dim]Session: {session}[/dim]")
    console.print()

    try:
        run_unified_manager(session_name=session)
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitor closed.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# =============================================================================
# Tasks Command
# =============================================================================


@app.command()
def tasks(
    kanban: bool = typer.Option(False, "--kanban", "-k", help="Show in kanban layout"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent task files to show"),
    all_tasks: bool = typer.Option(False, "--all", "-a", help="Show all task files"),
):
    """Show tasks from Claude Code's todo system."""
    loader = TaskLoader()

    if all_tasks:
        task_files = loader.load_all()
    else:
        task_files = loader.load_recent(limit)

    if not task_files:
        console.print("[yellow]No tasks found in ~/.claude/todos/[/yellow]")
        return

    if kanban:
        _show_kanban(task_files)
    else:
        _show_table(task_files)


def _show_kanban(task_files):
    """Display tasks in kanban columns."""
    all_tasks = []
    for tf in task_files:
        all_tasks.extend(tf.tasks)

    pending = [t for t in all_tasks if t.status == TaskStatus.PENDING]
    in_progress = [t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]
    completed = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]

    # Create kanban table
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column(f"📋 TODO ({len(pending)})", style="yellow", width=30)
    table.add_column(f"🔄 IN PROGRESS ({len(in_progress)})", style="blue", width=30)
    table.add_column(f"✅ DONE ({len(completed)})", style="green", width=30)

    max_rows = max(len(pending), len(in_progress), len(completed), 1)

    for i in range(max_rows):
        p = pending[i].content[:28] if i < len(pending) else ""
        ip = in_progress[i].content[:28] if i < len(in_progress) else ""
        c = completed[i].content[:28] if i < len(completed) else ""
        table.add_row(p, ip, c)

    total = len(all_tasks)
    progress_pct = int(len(completed) / total * 100) if total > 0 else 0

    console.print()
    console.print(Panel(
        table,
        title="[bold]Claude Agent Teams - Tasks[/bold]",
        subtitle=f"Progress: {progress_pct}% ({len(completed)}/{total})",
    ))
    console.print()


def _show_table(task_files):
    """Display tasks in table format."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=6)
    table.add_column("Status", width=15)
    table.add_column("Task", width=50)
    table.add_column("Active Form", width=30)

    for tf in task_files:
        for task in tf.tasks:
            status_color = {
                TaskStatus.PENDING: "yellow",
                TaskStatus.IN_PROGRESS: "blue",
                TaskStatus.COMPLETED: "green",
            }.get(task.status, "white")

            table.add_row(
                task.id,
                f"[{status_color}]{task.display_status}[/{status_color}]",
                task.content,
                task.active_form,
            )

    console.print()
    console.print(table)
    console.print()


# =============================================================================
# Stats Command
# =============================================================================


@app.command()
def stats(
    daily: bool = typer.Option(False, "--daily", "-d", help="Show daily activity breakdown"),
    tokens: bool = typer.Option(False, "--tokens", "-t", help="Show token usage by model"),
):
    """Show usage statistics from Claude Code."""
    loader = StatsLoader()
    stats_data = loader.load()

    if not stats_data:
        console.print("[yellow]No statistics found in ~/.claude/stats-cache.json[/yellow]")
        return

    # Summary panel
    summary = Table.grid(padding=(0, 2))
    summary.add_column()
    summary.add_column()
    summary.add_row("Total Sessions:", f"[bold]{stats_data.total_sessions:,}[/bold]")
    summary.add_row("Total Messages:", f"[bold]{stats_data.total_messages:,}[/bold]")
    summary.add_row("Last Updated:", f"[dim]{stats_data.last_computed_date or 'Unknown'}[/dim]")

    console.print()
    console.print(Panel(summary, title="[bold]Claude Code Statistics[/bold]"))

    if tokens:
        console.print()
        token_table = Table(title="Token Usage by Model", show_header=True)
        token_table.add_column("Model", style="cyan")
        token_table.add_column("Input", justify="right")
        token_table.add_column("Output", justify="right")
        token_table.add_column("Cache Read", justify="right")
        token_table.add_column("Total", justify="right", style="bold")

        for model, usage in stats_data.model_usage.items():
            short_name = model.replace("claude-", "").replace("-20", " (20")
            if "(" in short_name:
                short_name += ")"
            input_t = usage.get("inputTokens", 0)
            output_t = usage.get("outputTokens", 0)
            cache_t = usage.get("cacheReadInputTokens", 0)
            total = input_t + output_t

            token_table.add_row(
                short_name,
                f"{input_t:,}",
                f"{output_t:,}",
                f"{cache_t:,}",
                f"{total:,}",
            )

        console.print(token_table)

    if daily and stats_data.daily_activity:
        console.print()
        daily_table = Table(title="Recent Daily Activity", show_header=True)
        daily_table.add_column("Date", style="cyan")
        daily_table.add_column("Messages", justify="right")
        daily_table.add_column("Sessions", justify="right")
        daily_table.add_column("Tool Calls", justify="right")

        # Show last 7 days
        for day in stats_data.daily_activity[-7:]:
            daily_table.add_row(
                day.get("date", ""),
                str(day.get("messageCount", 0)),
                str(day.get("sessionCount", 0)),
                str(day.get("toolCallCount", 0)),
            )

        console.print(daily_table)

    console.print()


# =============================================================================
# Team Subcommands
# =============================================================================


team_app = typer.Typer(help="Team management commands")
app.add_typer(team_app, name="team")


@team_app.command("list")
def team_list():
    """List available team templates."""
    teams_dir = Path(__file__).parent.parent / "teams"

    table = Table(title="Available Team Templates", show_header=True)
    table.add_column("Team", style="cyan")
    table.add_column("Description", width=50)
    table.add_column("Roles")

    team_info = {
        "code-review": ("Parallel code review", "Security, Performance, Test Coverage"),
        "development": ("Feature development pipeline", "Architect, Implementer, Tester, Reviewer"),
        "research": ("Adversarial research", "Investigator, Devil's Advocate, Synthesizer"),
        "manager-led": ("Coordinated delegation", "Manager, Workers"),
        "software-dev": ("End-to-end development", "PM, Researcher, Architect, Dev, Tester, Reviewer"),
    }

    for team_name, (desc, roles) in team_info.items():
        team_path = teams_dir / team_name
        if team_path.exists():
            table.add_row(team_name, desc, roles)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Use 'catt team spawn <name>' to spawn a team[/dim]")
    console.print()


@team_app.command("spawn")
def team_spawn(
    name: str = typer.Argument(..., help="Team template name (e.g., 'dev', 'review')"),
):
    """Spawn a team from a template."""
    teams_dir = Path(__file__).parent.parent / "teams"

    # Resolve short names
    name_map = {
        "dev": "development",
        "review": "code-review",
        "research": "research",
        "manager": "manager-led",
        "software": "software-dev",
    }
    full_name = name_map.get(name, name)

    spawn_file = teams_dir / full_name / "spawn-prompt.md"

    if not spawn_file.exists():
        console.print(f"[red]Team template '{name}' not found[/red]")
        console.print("[dim]Use 'catt team list' to see available templates[/dim]")
        raise typer.Exit(1)

    # Read and display the spawn prompt
    content = spawn_file.read_text()

    console.print()
    console.print(Panel(
        content,
        title=f"[bold]Spawn Prompt: {full_name}[/bold]",
        subtitle="Copy this prompt to Claude Code",
    ))
    console.print()
    console.print("[dim]Copy the prompt above and paste it into Claude Code to spawn the team.[/dim]")
    console.print()


@team_app.command("status")
def team_status():
    """Show current team status."""
    # Check for active tasks as proxy for team activity
    loader = TaskLoader()
    active_tasks = loader.get_active_tasks()

    if not active_tasks:
        console.print("[yellow]No active tasks found. Team may not be running.[/yellow]")
        return

    console.print()
    console.print(Panel(
        f"[bold green]{len(active_tasks)}[/bold green] tasks currently in progress",
        title="[bold]Team Status[/bold]",
    ))

    table = Table(show_header=True)
    table.add_column("Task ID", style="dim")
    table.add_column("Description")
    table.add_column("Current Action", style="cyan")

    for task in active_tasks[:10]:
        table.add_row(task.id, task.content[:40], task.active_form[:40])

    console.print(table)
    console.print()


if __name__ == "__main__":
    app()
