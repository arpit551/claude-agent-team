"""Agent spawner for workflow execution."""

import logging
from pathlib import Path
from typing import Optional

from cat.agent.models import AgentConfig, AgentRole, AgentStatus
from cat.agent.registry import AgentRegistry
from cat.agent.controller import AgentController
from cat.interactive.config import ProjectConfig
from cat.workflow.exceptions import (
    AgentSpawnError,
    DependencyError,
    CircularDependencyError,
)
from cat.workflow.performance import timed, benchmark

logger = logging.getLogger(__name__)


class AgentSpawner:
    """Spawns agents using AgentController."""

    def __init__(
        self,
        config: ProjectConfig,
        controller: AgentController,
        registry: AgentRegistry,
    ):
        self.config = config
        self.controller = controller
        self.registry = registry

        # Validate configuration on initialization
        self._validate_dependencies()

    @timed("spawn_agent")
    def spawn_agent(
        self,
        agent_config: AgentConfig,
        additional_context: Optional[str] = None,
    ) -> bool:
        """Spawn a single agent using AgentController.

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
            # Validate working directory exists
            if not self.config.working_dir.exists():
                raise AgentSpawnError(
                    role,
                    f"Working directory does not exist: {self.config.working_dir}",
                )

            # Spawn agent via controller
            logger.info(f"Spawning {role.display_name} with model {agent_config.model.value}")
            agent_process = self.controller.spawn_agent(
                role=role.value,
                prompt=prompt,
                model=agent_config.model.value,
                working_dir=self.config.working_dir,
            )

            # Verify output file was created
            if not agent_process.output_file.exists():
                raise AgentSpawnError(
                    role,
                    "Output file was not created",
                )

            # Update registry with output file
            self.registry.update_status(role, AgentStatus.RUNNING)
            self.registry.set_output_file(role, agent_process.output_file)

            logger.info(f"Successfully spawned {role.display_name} (output: {agent_process.output_file})")
            return True

        except AgentSpawnError as e:
            # Already formatted error
            logger.error(f"Spawn error: {e}")
            self.registry.update_status(
                role,
                AgentStatus.FAILED,
                error_message=str(e)
            )
            return False

        except Exception as e:
            # Wrap unexpected errors
            error = AgentSpawnError(role, "Unexpected error", original_error=e)
            logger.error(f"Unexpected spawn error: {error}", exc_info=True)
            self.registry.update_status(
                role,
                AgentStatus.FAILED,
                error_message=str(error)
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

    def _validate_dependencies(self) -> None:
        """Validate agent dependencies for circular references and validity.

        Raises:
            CircularDependencyError: If circular dependency detected
            DependencyError: If invalid dependency found
        """
        workflow = self.config.agent_workflow_order
        agent_roles = {agent.role.value for agent in workflow}

        # Check for circular dependencies using DFS
        for agent_config in workflow:
            visited = set()
            path = []
            if self._has_cycle(agent_config.role.value, visited, path, workflow):
                raise CircularDependencyError(path + [agent_config.role.value])

            # Check all dependencies exist
            for dep in agent_config.depends_on:
                if dep not in agent_roles:
                    raise DependencyError(
                        agent_config.role,
                        missing_dependencies=[dep],
                    )

    def _has_cycle(
        self,
        role: str,
        visited: set[str],
        path: list[str],
        workflow: list[AgentConfig],
    ) -> bool:
        """Check for circular dependencies using DFS.

        Args:
            role: Current role being checked
            visited: Set of visited roles in current path
            path: Current dependency path
            workflow: All agent configs

        Returns:
            True if cycle detected
        """
        if role in visited:
            return True

        visited.add(role)
        path.append(role)

        # Find config for this role
        config = next((a for a in workflow if a.role.value == role), None)
        if config:
            for dep in config.depends_on:
                if self._has_cycle(dep, visited, path, workflow):
                    return True

        visited.remove(role)
        path.pop()
        return False
