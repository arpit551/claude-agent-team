#!/usr/bin/env python3
"""Demo the new Tmux Manager UI with real agents."""

import time
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

from cat.agent.tmux import TmuxController


def spawn_demo_agents():
    """Spawn demo agents for testing the UI."""
    print("🚀 Spawning demo agents...")
    print()

    controller = TmuxController(session_name="catt-demo")
    controller.kill_session()
    controller.create_session()

    # Spawn agents with realistic prompts
    agents = [
        ("researcher", "You are a research agent. Start by saying 'Researcher ready!' then research Python async patterns.", "opus"),
        ("architect", "You are an architect agent. Start by saying 'Architect ready!' then design a microservice architecture.", "opus"),
        ("developer", "You are a developer agent. Start by saying 'Developer ready!' then implement a simple API endpoint.", "sonnet"),
        ("tester", "You are a tester agent. Start by saying 'Tester ready!' then write pytest tests.", "sonnet"),
    ]

    for role, prompt, model in agents:
        print(f"  ✓ Spawning {role} ({model})...")
        controller.spawn_agent(role, prompt, model)
        time.sleep(0.5)

    print()
    print("✅ All agents spawned!")
    print()
    print("Now run:")
    print("  catt tmux --session catt-demo")
    print()
    print("Or with default session:")
    print("  catt tmux")
    print()
    print("To see the interactive UI for managing these agents!")
    print()

    return controller


if __name__ == "__main__":
    try:
        controller = spawn_demo_agents()

        print("Agents are running. Press Ctrl+C to cleanup...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🧹 Cleaning up...")
        controller.kill_session()
        print("✓ Done!")
