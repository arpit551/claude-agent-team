"""Project configuration for Claude Agent Teams."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from cat.agent.models import AgentConfig, AgentRole, get_default_agent_configs


@dataclass
class PerformanceSettings:
    """Performance optimization settings."""

    cache_enabled: bool = True
    cache_ttl: float = 1.0  # seconds
    benchmark_enabled: bool = False

    def to_dict(self) -> dict:
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "benchmark_enabled": self.benchmark_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PerformanceSettings":
        return cls(
            cache_enabled=data.get("cache_enabled", True),
            cache_ttl=data.get("cache_ttl", 1.0),
            benchmark_enabled=data.get("benchmark_enabled", False),
        )


@dataclass
class WatcherSettings:
    """File watcher settings."""

    enabled: bool = True
    use_watchdog: bool = True
    poll_interval: float = 2.0  # seconds

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "use_watchdog": self.use_watchdog,
            "poll_interval": self.poll_interval,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatcherSettings":
        return cls(
            enabled=data.get("enabled", True),
            use_watchdog=data.get("use_watchdog", True),
            poll_interval=data.get("poll_interval", 2.0),
        )


@dataclass
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "INFO"
    file: str = ".catt/logs/catt.log"
    colored: bool = True
    rotate_size: int = 10485760  # 10MB
    backup_count: int = 5

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "file": self.file,
            "colored": self.colored,
            "rotate_size": self.rotate_size,
            "backup_count": self.backup_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingSettings":
        return cls(
            level=data.get("level", "INFO"),
            file=data.get("file", ".catt/logs/catt.log"),
            colored=data.get("colored", True),
            rotate_size=data.get("rotate_size", 10485760),
            backup_count=data.get("backup_count", 5),
        )


@dataclass
class WorkflowSettings:
    """Workflow execution settings."""

    fail_fast: bool = False
    agent_timeout: int = 3600  # seconds
    max_iterations: int = 40

    def to_dict(self) -> dict:
        return {
            "fail_fast": self.fail_fast,
            "agent_timeout": self.agent_timeout,
            "max_iterations": self.max_iterations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowSettings":
        return cls(
            fail_fast=data.get("fail_fast", False),
            agent_timeout=data.get("agent_timeout", 3600),
            max_iterations=data.get("max_iterations", 40),
        )


class UseCase(str):
    """Use case types for project initialization."""

    BUILD_FEATURE = "build_feature"
    REFACTOR = "refactor"
    RESEARCH = "research"
    BUG_FIX = "bug_fix"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Get list of (value, display_name) tuples."""
        return [
            (cls.BUILD_FEATURE, "Build a new feature"),
            (cls.REFACTOR, "Refactor existing code"),
            (cls.RESEARCH, "Research & evaluate options"),
            (cls.BUG_FIX, "Fix bugs"),
        ]


@dataclass
class ProjectConfig:
    """Project-level configuration for CATT."""

    name: str
    description: str
    use_case: str
    agents: dict[str, AgentConfig] = field(default_factory=dict)
    output_dir: Path = field(default_factory=lambda: Path(".catt/output"))
    max_total_iterations: int = 200
    created_at: Optional[datetime] = None
    working_dir: Optional[Path] = None
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    watcher: WatcherSettings = field(default_factory=WatcherSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    workflow: WorkflowSettings = field(default_factory=WorkflowSettings)

    def __post_init__(self):
        """Initialize defaults."""
        if not self.agents:
            self.agents = get_default_agent_configs()
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.working_dir is None:
            self.working_dir = Path.cwd()
        if not isinstance(self.performance, PerformanceSettings):
            self.performance = PerformanceSettings()
        if not isinstance(self.watcher, WatcherSettings):
            self.watcher = WatcherSettings()
        if not isinstance(self.logging, LoggingSettings):
            self.logging = LoggingSettings()
        if not isinstance(self.workflow, WorkflowSettings):
            self.workflow = WorkflowSettings()

    @property
    def config_dir(self) -> Path:
        """Get the .catt config directory."""
        return self.working_dir / ".catt"

    @property
    def config_file(self) -> Path:
        """Get the project.yaml file path."""
        return self.config_dir / "project.yaml"

    @property
    def state_file(self) -> Path:
        """Get the state.json file path."""
        return self.config_dir / "state.json"

    @property
    def enabled_agents(self) -> list[AgentConfig]:
        """Get list of enabled agents."""
        return [a for a in self.agents.values() if a.enabled]

    @property
    def agent_workflow_order(self) -> list[AgentConfig]:
        """Get agents in workflow execution order (topological sort)."""
        # Simple topological sort based on dependencies
        result = []
        visited = set()

        def visit(agent: AgentConfig):
            if agent.role.value in visited:
                return
            visited.add(agent.role.value)

            # Visit dependencies first
            for dep_role in agent.depends_on:
                if dep_role in self.agents:
                    visit(self.agents[dep_role])

            if agent.enabled:
                result.append(agent)

        for agent in self.agents.values():
            visit(agent)

        return result

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "use_case": self.use_case,
            "agents": {
                role: config.to_dict()
                for role, config in self.agents.items()
            },
            "output_dir": str(self.output_dir),
            "max_total_iterations": self.max_total_iterations,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "working_dir": str(self.working_dir) if self.working_dir else None,
            "performance": self.performance.to_dict(),
            "watcher": self.watcher.to_dict(),
            "logging": self.logging.to_dict(),
            "workflow": self.workflow.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Create from dictionary."""
        agents = {}
        for role, config_data in data.get("agents", {}).items():
            agents[role] = AgentConfig.from_dict(config_data)

        return cls(
            name=data["name"],
            description=data["description"],
            use_case=data["use_case"],
            agents=agents,
            output_dir=Path(data.get("output_dir", ".catt/output")),
            max_total_iterations=data.get("max_total_iterations", 200),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            working_dir=Path(data["working_dir"]) if data.get("working_dir") else None,
            performance=PerformanceSettings.from_dict(data.get("performance", {})),
            watcher=WatcherSettings.from_dict(data.get("watcher", {})),
            logging=LoggingSettings.from_dict(data.get("logging", {})),
            workflow=WorkflowSettings.from_dict(data.get("workflow", {})),
        )

    def save(self, path: Optional[Path] = None) -> Path:
        """Save configuration to YAML file."""
        save_path = path or self.config_file
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

        return save_path

    @classmethod
    def load(cls, path: Path) -> "ProjectConfig":
        """Load configuration from YAML file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")

        if not data or not isinstance(data, dict):
            raise ValueError(f"Invalid config format in {path}: expected a YAML dictionary")

        config = cls.from_dict(data)
        # Set working dir to parent of .catt directory
        config.working_dir = path.parent.parent

        # Validate dependencies
        config.validate_dependencies()
        return config

    def validate_dependencies(self) -> None:
        """Validate that all dependencies reference existing agents."""
        valid_roles = set(self.agents.keys())
        warnings = []

        for role, agent_config in self.agents.items():
            for dep in agent_config.depends_on:
                if dep not in valid_roles:
                    warnings.append(f"Agent '{role}' depends on unknown agent '{dep}'")

        if warnings:
            import sys
            for warning in warnings:
                print(f"[yellow]Warning: {warning}[/yellow]", file=sys.stderr)

    @classmethod
    def find_config(cls, start_dir: Optional[Path] = None) -> Optional[Path]:
        """Find project.yaml file in current or parent directories."""
        current = start_dir or Path.cwd()

        while current != current.parent:
            config_path = current / ".catt" / "project.yaml"
            if config_path.exists():
                return config_path
            current = current.parent

        return None

    @classmethod
    def load_or_none(cls, start_dir: Optional[Path] = None) -> Optional["ProjectConfig"]:
        """Load config if it exists, otherwise return None."""
        config_path = cls.find_config(start_dir)
        if config_path:
            return cls.load(config_path)
        return None

    def ensure_directories(self) -> None:
        """Create necessary directories."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "output").mkdir(exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)

    def get_agent_prompt(self, role: AgentRole) -> str:
        """Get the prompt for spawning an agent."""
        prompts = {
            AgentRole.RESEARCHER: f"""You are a Researcher agent on a development team.

Project: {self.name}
Description: {self.description}
Use Case: {self.use_case}

Your task:
1. Research technical options and approaches for this project
2. Evaluate feasibility, trade-offs, and risks
3. Document your findings clearly
4. When complete, output: <promise>RESEARCH_COMPLETE</promise>

Focus on providing evidence-based recommendations.""",

            AgentRole.MANAGER: f"""You are a Manager agent coordinating a development team.

Project: {self.name}
Description: {self.description}
Use Case: {self.use_case}

Your task:
1. Review the research findings in .catt/output/research.md
2. Break down the project into specific, actionable tasks
3. Assign tasks to appropriate roles (architect, developer, tester, reviewer)
4. Define task dependencies
5. When complete, output: <promise>TASKS_CREATED</promise>

Create optimal 15-45 minute tasks with clear deliverables.""",

            AgentRole.ARCHITECT: f"""You are an Architect agent on a development team.

Project: {self.name}
Description: {self.description}

Your task:
1. Review the task plan in .catt/output/tasks.md
2. Design the system architecture for your assigned tasks
3. Define interfaces, data models, and patterns
4. Document in .catt/output/architecture.md
5. When complete, output: <promise>ARCHITECTURE_COMPLETE</promise>

Focus on clean, maintainable design.""",

            AgentRole.DEVELOPER: f"""You are a Developer agent on a development team.

Project: {self.name}
Description: {self.description}

Your task:
1. Review the architecture in .catt/output/architecture.md
2. Implement your assigned tasks following the design
3. Write clean, well-documented code
4. When complete, output: <promise>IMPLEMENTATION_COMPLETE</promise>

Follow existing code patterns and conventions.""",

            AgentRole.TESTER: f"""You are a Tester agent on a development team.

Project: {self.name}
Description: {self.description}

Your task:
1. Review the implementation
2. Write comprehensive tests (unit, integration)
3. Cover edge cases and error conditions
4. Ensure all tests pass
5. When complete, output: <promise>TESTING_COMPLETE</promise>

Aim for high test coverage.""",

            AgentRole.REVIEWER: f"""You are a Reviewer agent on a development team.

Project: {self.name}
Description: {self.description}

Your task:
1. Review all code changes for quality and security
2. Check for OWASP vulnerabilities
3. Verify code follows best practices
4. Document any issues found
5. When complete, output: <promise>REVIEW_COMPLETE</promise>

Be thorough but constructive.""",
        }

        return prompts.get(role, f"You are a {role.display_name} agent.")

    def get_completion_signal(self, role: AgentRole) -> str:
        """Get the completion signal for an agent role."""
        signals = {
            AgentRole.RESEARCHER: "RESEARCH_COMPLETE",
            AgentRole.MANAGER: "TASKS_CREATED",
            AgentRole.PRODUCT_MANAGER: "REQUIREMENTS_COMPLETE",
            AgentRole.ARCHITECT: "ARCHITECTURE_COMPLETE",
            AgentRole.DEVELOPER: "IMPLEMENTATION_COMPLETE",
            AgentRole.TESTER: "TESTING_COMPLETE",
            AgentRole.REVIEWER: "REVIEW_COMPLETE",
        }
        return signals.get(role, "DONE")

    def generate_team_prompt(self) -> str:
        """Generate a prompt to create an agent team using Claude Code's built-in feature."""
        enabled = self.enabled_agents

        # Build teammate descriptions
        teammates = []
        for agent in enabled:
            model_note = f"Use {agent.model.value.title()} for this teammate." if agent.model else ""
            teammates.append(f"- **{agent.role.display_name}**: {self._get_role_description(agent.role)}. {model_note}")

        teammates_str = "\n".join(teammates)

        # Build the team creation prompt
        prompt = f"""Create an agent team to build this project:

## Project: {self.name}
{self.description}

## Task
{self._get_use_case_description()}

## Team Structure
Spawn the following teammates:
{teammates_str}

## Coordination
1. Start with research/planning teammates first
2. Use the shared task list to coordinate work
3. Have teammates message each other when they complete dependencies
4. The researcher should document findings before others start
5. The developer should wait for architecture to be complete
6. The tester should wait for implementation
7. The reviewer does final quality check

## Working Directory
All work should be done in: {self.working_dir}

Create output files in: {self.working_dir}/.catt/output/

Begin by spawning the team and coordinating their work."""

        return prompt

    def _get_role_description(self, role: AgentRole) -> str:
        """Get a short description for each role."""
        descriptions = {
            AgentRole.RESEARCHER: "Research technical options, evaluate trade-offs, document findings",
            AgentRole.MANAGER: "Break down work into tasks, coordinate the team, track progress",
            AgentRole.PRODUCT_MANAGER: "Define requirements, user stories, acceptance criteria",
            AgentRole.ARCHITECT: "Design system architecture, define interfaces and patterns",
            AgentRole.DEVELOPER: "Implement features, write clean code following the architecture",
            AgentRole.TESTER: "Write comprehensive tests, ensure quality and coverage",
            AgentRole.REVIEWER: "Review code for quality, security, and best practices",
        }
        return descriptions.get(role, "Assist with development tasks")

    def _get_use_case_description(self) -> str:
        """Get description based on use case."""
        descriptions = {
            UseCase.BUILD_FEATURE: "Build a new feature from scratch. Research options, design architecture, implement, test, and review.",
            UseCase.REFACTOR: "Refactor and improve existing code. Analyze current state, design improvements, implement changes safely.",
            UseCase.RESEARCH: "Research and evaluate technical options. Compare alternatives, assess trade-offs, provide recommendations.",
            UseCase.BUG_FIX: "Investigate and fix bugs. Reproduce issues, identify root causes, implement fixes, add regression tests.",
        }
        return descriptions.get(self.use_case, "Complete the development task.")
