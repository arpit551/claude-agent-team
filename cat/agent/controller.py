"""Agent controller for spawning and managing Claude Code agents."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AgentProcess:
    """Represents a spawned agent process."""

    role: str
    task_id: str
    working_dir: Path
    output_file: Path
    started_at: float
    process: Optional[subprocess.Popen] = None

    @property
    def is_running(self) -> bool:
        """Check if process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds."""
        return int(time.time() - self.started_at)


class AgentController:
    """Controller for spawning Claude Code agents via Task tool API."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the controller.

        Args:
            output_dir: Directory for agent output files
        """
        if output_dir is None:
            output_dir = Path.cwd() / ".catt" / "output"
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agents: dict[str, AgentProcess] = {}

    def spawn_agent(
        self,
        role: str,
        prompt: str,
        model: str = "sonnet",
        working_dir: Optional[Path] = None,
    ) -> AgentProcess:
        """Spawn a new agent using Claude Code.

        This is a simplified implementation. In practice, this would:
        1. Use the Task tool API to spawn a subprocess
        2. Pass the prompt and model configuration
        3. Capture output to a file

        Args:
            role: Agent role name
            prompt: Agent prompt/instructions
            model: Model type ("opus", "sonnet", "haiku")
            working_dir: Working directory for agent

        Returns:
            AgentProcess instance
        """
        if working_dir is None:
            working_dir = Path.cwd()

        # Generate unique task ID
        task_id = f"{role}_{int(time.time())}"

        # Create output file
        output_file = self.output_dir / f"{role}.log"

        # Write the prompt to a file for the agent to read
        prompt_file = self.output_dir / f"{role}_prompt.txt"
        prompt_file.write_text(prompt)

        # In a real implementation, this would use the Task tool
        # For now, we create a placeholder process
        agent_process = AgentProcess(
            role=role,
            task_id=task_id,
            working_dir=working_dir,
            output_file=output_file,
            started_at=time.time(),
            process=None,  # Would be subprocess.Popen in real impl
        )

        self.agents[role] = agent_process
        return agent_process

    def get_agent(self, role: str) -> Optional[AgentProcess]:
        """Get an agent process by role.

        Args:
            role: Agent role name

        Returns:
            AgentProcess or None if not found
        """
        return self.agents.get(role)

    def kill_agent(self, role: str) -> bool:
        """Kill an agent process.

        Args:
            role: Agent role name

        Returns:
            True if killed successfully
        """
        agent = self.agents.get(role)
        if not agent:
            return False

        if agent.process:
            try:
                agent.process.terminate()
                agent.process.wait(timeout=5)
                return True
            except Exception:
                try:
                    agent.process.kill()
                    return True
                except Exception:
                    return False

        return True

    def kill_all(self) -> None:
        """Kill all spawned agents."""
        for role in list(self.agents.keys()):
            self.kill_agent(role)

    def capture_output(self, role: str, lines: int = 100) -> str:
        """Capture recent output from an agent.

        Args:
            role: Agent role name
            lines: Number of lines to read

        Returns:
            Output text
        """
        agent = self.agents.get(role)
        if not agent:
            return ""

        output_file = agent.output_file
        if not output_file.exists():
            return ""

        try:
            with open(output_file) as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception:
            return ""

    def is_agent_running(self, role: str) -> bool:
        """Check if an agent is still running.

        Args:
            role: Agent role name

        Returns:
            True if running
        """
        agent = self.agents.get(role)
        if not agent:
            return False
        return agent.is_running

    def list_agents(self) -> list[AgentProcess]:
        """List all spawned agents.

        Returns:
            List of AgentProcess instances
        """
        return list(self.agents.values())

    def cleanup(self) -> None:
        """Clean up all agents and resources."""
        self.kill_all()
        self.agents.clear()


# Singleton instance
_controller: Optional[AgentController] = None


def get_agent_controller(output_dir: Optional[Path] = None) -> AgentController:
    """Get the singleton AgentController instance.

    Args:
        output_dir: Directory for agent output files

    Returns:
        AgentController instance
    """
    global _controller
    if _controller is None:
        _controller = AgentController(output_dir)
    return _controller
