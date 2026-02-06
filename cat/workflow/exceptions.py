"""Workflow-specific exceptions with detailed error information."""

from typing import Optional
from cat.agent.models import AgentRole


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    def __init__(self, message: str, recoverable: bool = False):
        super().__init__(message)
        self.recoverable = recoverable


class AgentSpawnError(WorkflowError):
    """Error spawning an agent."""

    def __init__(
        self,
        role: AgentRole,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        self.role = role
        self.reason = reason
        self.original_error = original_error

        message = f"Failed to spawn {role.display_name}: {reason}"
        if original_error:
            message += f" ({type(original_error).__name__}: {original_error})"

        super().__init__(message, recoverable=True)


class AgentTimeoutError(WorkflowError):
    """Agent exceeded maximum execution time."""

    def __init__(
        self,
        role: AgentRole,
        timeout_seconds: int,
        iteration_count: int = 0,
    ):
        self.role = role
        self.timeout_seconds = timeout_seconds
        self.iteration_count = iteration_count

        message = (
            f"{role.display_name} timed out after {timeout_seconds}s "
            f"({iteration_count} iterations)"
        )
        super().__init__(message, recoverable=False)


class DependencyError(WorkflowError):
    """Agent dependency requirements not met."""

    def __init__(
        self,
        role: AgentRole,
        missing_dependencies: list[str],
        failed_dependencies: list[str] = None,
    ):
        self.role = role
        self.missing_dependencies = missing_dependencies
        self.failed_dependencies = failed_dependencies or []

        parts = []
        if missing_dependencies:
            parts.append(f"missing: {', '.join(missing_dependencies)}")
        if failed_dependencies:
            parts.append(f"failed: {', '.join(failed_dependencies)}")

        message = f"{role.display_name} cannot start - {', '.join(parts)}"
        super().__init__(message, recoverable=True)


class ConfigurationError(WorkflowError):
    """Configuration file or data is invalid."""

    def __init__(self, reason: str, file_path: Optional[str] = None):
        self.file_path = file_path
        self.reason = reason

        message = f"Configuration error: {reason}"
        if file_path:
            message += f" (in {file_path})"

        super().__init__(message, recoverable=False)


class StateError(WorkflowError):
    """Workflow state is corrupted or invalid."""

    def __init__(self, reason: str):
        super().__init__(f"State error: {reason}", recoverable=False)


class OutputCollectionError(WorkflowError):
    """Error collecting agent output."""

    def __init__(
        self,
        role: AgentRole,
        reason: str,
        original_error: Optional[Exception] = None,
    ):
        self.role = role
        self.reason = reason
        self.original_error = original_error

        message = f"Failed to collect output from {role.display_name}: {reason}"
        if original_error:
            message += f" ({type(original_error).__name__})"

        super().__init__(message, recoverable=True)


class ProcessError(WorkflowError):
    """Error with underlying agent process."""

    def __init__(
        self,
        role: AgentRole,
        pid: Optional[int],
        reason: str,
    ):
        self.role = role
        self.pid = pid
        self.reason = reason

        message = f"Process error for {role.display_name}"
        if pid:
            message += f" (PID {pid})"
        message += f": {reason}"

        super().__init__(message, recoverable=False)


class WorkflowTimeoutError(WorkflowError):
    """Entire workflow exceeded maximum time."""

    def __init__(
        self,
        total_iterations: int,
        max_iterations: int,
        completed_count: int,
        total_count: int,
    ):
        self.total_iterations = total_iterations
        self.max_iterations = max_iterations
        self.completed_count = completed_count
        self.total_count = total_count

        message = (
            f"Workflow timeout after {total_iterations} iterations "
            f"(max: {max_iterations}). "
            f"Completed {completed_count}/{total_count} agents."
        )
        super().__init__(message, recoverable=False)


class CircularDependencyError(WorkflowError):
    """Circular dependency detected in agent workflow."""

    def __init__(self, cycle: list[str]):
        self.cycle = cycle

        message = f"Circular dependency detected: {' -> '.join(cycle)}"
        super().__init__(message, recoverable=False)
