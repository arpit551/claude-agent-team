"""Interactive wizard for project initialization."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from cat.agent.models import AgentConfig, AgentRole, ModelType, get_default_agent_configs
from cat.interactive.config import ProjectConfig, UseCase


class InitWizard:
    """Interactive wizard for initializing a CATT project."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def run(self, working_dir: Optional[Path] = None) -> Optional[ProjectConfig]:
        """Run the interactive wizard and return project config."""
        working_dir = working_dir or Path.cwd()

        # Check if config already exists
        existing_config = ProjectConfig.find_config(working_dir)
        if existing_config:
            self.console.print(f"\n[yellow]Config already exists at {existing_config}[/yellow]")
            if not Confirm.ask("Overwrite existing configuration?", default=False):
                return None

        self.console.print()
        self.console.print(Panel(
            "[bold cyan]Claude Agent Teams - Initialize[/bold cyan]\n\n"
            "This wizard will help you set up a new CATT project.\n"
            "You can configure which agents to enable and their settings.",
            title="Welcome",
        ))
        self.console.print()

        # Step 1: Project basics
        name = self._ask_project_name()
        description = self._ask_description()
        use_case = self._ask_use_case()

        # Step 2: Agent configuration
        agents = self._ask_agents()

        # Step 3: Iteration settings
        max_iterations = self._ask_max_iterations()

        # Create config
        config = ProjectConfig(
            name=name,
            description=description,
            use_case=use_case,
            agents=agents,
            max_total_iterations=max_iterations * len([a for a in agents.values() if a.enabled]),
            working_dir=working_dir,
        )

        # Step 4: Confirmation
        self._show_summary(config)

        if not Confirm.ask("\n[bold]Create project with this configuration?[/bold]", default=True):
            self.console.print("[yellow]Cancelled[/yellow]")
            return None

        # Save config
        config.ensure_directories()
        config_path = config.save()

        self.console.print()
        self.console.print(f"[green]✓[/green] Config saved to [cyan]{config_path}[/cyan]")
        self.console.print()
        self.console.print("Next steps:")
        self.console.print("  [cyan]catt run --dry-run[/cyan]  Show execution plan")
        self.console.print("  [cyan]catt run[/cyan]            Start the workflow")
        self.console.print("  [cyan]catt dashboard[/cyan]      Monitor progress")
        self.console.print()

        return config

    def _ask_project_name(self) -> str:
        """Ask for project name."""
        # Suggest name based on current directory
        default = Path.cwd().name.replace(" ", "-").lower()
        return Prompt.ask(
            "[bold]Project name[/bold]",
            default=default,
        )

    def _ask_description(self) -> str:
        """Ask for project description."""
        return Prompt.ask(
            "[bold]Project description[/bold]",
            default="",
        )

    def _ask_use_case(self) -> str:
        """Ask for use case type."""
        self.console.print("\n[bold]What do you want to do?[/bold]")
        choices = UseCase.choices()

        for i, (value, label) in enumerate(choices, 1):
            self.console.print(f"  [cyan]{i}[/cyan]. {label}")

        while True:
            choice = Prompt.ask(
                "Select option",
                choices=[str(i) for i in range(1, len(choices) + 1)],
                default="1",
            )
            return choices[int(choice) - 1][0]

    def _ask_agents(self) -> dict[str, AgentConfig]:
        """Ask which agents to enable and configure."""
        self.console.print("\n[bold]Select agents to enable:[/bold]")
        self.console.print("[dim](Use recommended defaults for typical software development)[/dim]\n")

        agents = get_default_agent_configs()

        # Show agent selection
        for role in AgentRole:
            config = agents[role.value]
            default_enabled = role in (
                AgentRole.RESEARCHER,
                AgentRole.MANAGER,
                AgentRole.ARCHITECT,
                AgentRole.DEVELOPER,
                AgentRole.TESTER,
                AgentRole.REVIEWER,
            )

            model_str = f"[dim]({config.model.value})[/dim]"
            enabled = Confirm.ask(
                f"  {role.display_name:18} {model_str:12} - {role.description}",
                default=default_enabled,
            )
            config.enabled = enabled

        # Ask about model customization
        self.console.print()
        if Confirm.ask("Customize model assignments?", default=False):
            self._customize_models(agents)

        return agents

    def _customize_models(self, agents: dict[str, AgentConfig]) -> None:
        """Allow customizing model for each agent."""
        self.console.print("\n[bold]Model assignment:[/bold]")
        self.console.print("[dim]opus = complex reasoning, sonnet = efficient execution[/dim]\n")

        for role in AgentRole:
            config = agents[role.value]
            if not config.enabled:
                continue

            current = config.model.value
            choice = Prompt.ask(
                f"  {role.display_name}",
                choices=["opus", "sonnet"],
                default=current,
            )
            config.model = ModelType(choice)

    def _ask_max_iterations(self) -> int:
        """Ask for max iterations per agent."""
        self.console.print()
        return IntPrompt.ask(
            "[bold]Max iterations per agent[/bold]",
            default=40,
        )

    def _show_summary(self, config: ProjectConfig) -> None:
        """Show configuration summary."""
        self.console.print()

        # Project info
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bold")
        info_table.add_column()
        info_table.add_row("Project:", config.name)
        info_table.add_row("Description:", config.description or "[dim]none[/dim]")
        info_table.add_row("Use case:", config.use_case.replace("_", " ").title())
        info_table.add_row("Output dir:", str(config.output_dir))

        self.console.print(Panel(info_table, title="[bold]Project Summary[/bold]"))

        # Agent table
        agent_table = Table(title="Enabled Agents", show_header=True)
        agent_table.add_column("Role", style="cyan")
        agent_table.add_column("Model")
        agent_table.add_column("Dependencies")
        agent_table.add_column("Max Iterations", justify="right")

        workflow_agents = config.agent_workflow_order
        for agent in workflow_agents:
            deps = ", ".join(agent.depends_on) if agent.depends_on else "-"
            agent_table.add_row(
                agent.role.display_name,
                agent.model.value,
                deps,
                str(agent.max_iterations),
            )

        self.console.print()
        self.console.print(agent_table)

        # Workflow preview
        self.console.print()
        workflow_str = " → ".join(a.role.display_name for a in workflow_agents)
        self.console.print(f"[bold]Workflow:[/bold] {workflow_str}")


def run_wizard(working_dir: Optional[Path] = None) -> Optional[ProjectConfig]:
    """Convenience function to run the wizard."""
    wizard = InitWizard()
    return wizard.run(working_dir)
