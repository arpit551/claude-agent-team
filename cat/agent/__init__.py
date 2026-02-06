"""Agent module for Claude Agent Teams."""

from cat.agent.models import (
    AgentConfig,
    AgentRole,
    AgentState,
    AgentStatus,
    ModelType,
    get_default_agent_configs,
)
from cat.agent.registry import AgentRegistry, get_registry
from cat.agent.controller import AgentController, AgentProcess, get_agent_controller
from cat.agent.claude_monitor import (
    ClaudeStateReader,
    ClaudeSession,
    AgentOutputMonitor,
)

__all__ = [
    "AgentConfig",
    "AgentController",
    "AgentOutputMonitor",
    "AgentProcess",
    "AgentRegistry",
    "AgentRole",
    "AgentState",
    "AgentStatus",
    "ClaudeSession",
    "ClaudeStateReader",
    "ModelType",
    "get_agent_controller",
    "get_default_agent_configs",
    "get_registry",
]
