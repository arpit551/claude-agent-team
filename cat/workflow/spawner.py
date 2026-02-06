"""Agent spawner for workflow execution."""

from pathlib import Path
from typing import Optional

from cat.agent.models import AgentConfig, AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry
from cat.agent.tmux import TmuxController
from cat.interactive.config import ProjectConfig


class AgentSpawner:
    """Spawns agents in tmux based on workflow configuration."""

    def __init__(
        self,
        config: ProjectConfig,
        tmux: TmuxController,
        registry: AgentRegistry,
    ):
        self.config = config
        self.tmux = tmux
        self.registry = registry

    def spawn_agent(
        self,
        agent_config: AgentConfig,
        additional_context: Optional[str] = None,
    ) -> bool:
        """Spawn a single agent in tmux.

        Args:
            agent_config: Agent configuration
            additional_context: Additional context to add to prompt

        Returns:
            True if spawned successfully
        """
        role = agent_config.role

        # Update registry
        self.registry.update_status(role, AgentStatus.STARTING)

        # Build prompt
        prompt = self.config.get_agent_prompt(role)
        if additional_context:
            prompt += f"\n\nAdditional Context:\n{additional_context}"

        try:
            # Spawn in tmux
            pane = self.tmux.spawn_agent(
                role=role.value,
                prompt=prompt,
                model=agent_config.model.value,
                working_dir=self.config.working_dir,
            )

            # Update registry with pane info
            self.registry.set_tmux_pane(role, pane.target)
            self.registry.update_status(role, AgentStatus.RUNNING)

            # Set up output file
            output_file = self.config.config_dir / "output" / f"{role.value}.md"
            self.registry.set_output_file(role, output_file)

            return True

        except Exception as e:
            self.registry.update_status(
                role,
                AgentStatus.FAILED,
                error_message=str(e)
            )
            return False

    def spawn_workflow(self) -> list[AgentRole]:
        """Spawn agents in workflow order, respecting dependencies.

        Returns:
            List of roles that were spawned
        """
        spawned = []
        workflow = self.config.agent_workflow_order

        for agent_config in workflow:
            role = agent_config.role

            # Check dependencies
            if not self._dependencies_met(agent_config):
                self.registry.update_status(role, AgentStatus.WAITING)
                continue

            # Spawn the agent
            if self.spawn_agent(agent_config):
                spawned.append(role)

        return spawned

    def spawn_next_ready(self) -> Optional[AgentRole]:
        """Spawn the next agent that's ready (dependencies met).

        Returns:
            Role that was spawned, or None
        """
        workflow = self.config.agent_workflow_order

        for agent_config in workflow:
            role = agent_config.role
            state = self.registry.get(role)

            # Skip if already started or completed
            if state and state.status not in (AgentStatus.IDLE, AgentStatus.WAITING):
                continue

            # Check dependencies
            if not self._dependencies_met(agent_config):
                continue

            # Spawn this agent
            if self.spawn_agent(agent_config):
                return role

        return None

    def _dependencies_met(self, agent_config: AgentConfig) -> bool:
        """Check if agent's dependencies are satisfied.

        Args:
            agent_config: Agent configuration

        Returns:
            True if all dependencies are completed
        """
        for dep_role_str in agent_config.depends_on:
            try:
                dep_role = AgentRole(dep_role_str)
            except ValueError:
                continue

            dep_state = self.registry.get(dep_role)
            if dep_state is None or dep_state.status != AgentStatus.COMPLETED:
                return False

        return True

    def get_ready_agents(self) -> list[AgentConfig]:
        """Get list of agents ready to spawn.

        Returns:
            List of agent configs ready to spawn
        """
        ready = []
        workflow = self.config.agent_workflow_order

        for agent_config in workflow:
            role = agent_config.role
            state = self.registry.get(role)

            # Skip if already started
            if state and state.status not in (AgentStatus.IDLE, AgentStatus.WAITING):
                continue

            # Check dependencies
            if self._dependencies_met(agent_config):
                ready.append(agent_config)

        return ready

    def get_blocked_agents(self) -> list[tuple[AgentConfig, list[str]]]:
        """Get list of agents blocked by dependencies.

        Returns:
            List of (agent_config, missing_deps) tuples
        """
        blocked = []
        workflow = self.config.agent_workflow_order

        for agent_config in workflow:
            role = agent_config.role
            state = self.registry.get(role)

            # Skip if already started
            if state and state.status not in (AgentStatus.IDLE, AgentStatus.WAITING):
                continue

            # Find missing dependencies
            missing = []
            for dep_role_str in agent_config.depends_on:
                try:
                    dep_role = AgentRole(dep_role_str)
                except ValueError:
                    continue

                dep_state = self.registry.get(dep_role)
                if dep_state is None or dep_state.status != AgentStatus.COMPLETED:
                    missing.append(dep_role_str)

            if missing:
                blocked.append((agent_config, missing))

        return blocked
