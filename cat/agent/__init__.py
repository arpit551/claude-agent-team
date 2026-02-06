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
from cat.agent.tmux import TmuxController, TmuxPane, get_tmux_controller

__all__ = [
    "AgentConfig",
    "AgentRegistry",
    "AgentRole",
    "AgentState",
    "AgentStatus",
    "ModelType",
    "TmuxController",
    "TmuxPane",
    "get_default_agent_configs",
    "get_registry",
    "get_tmux_controller",
]
