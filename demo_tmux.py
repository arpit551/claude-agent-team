#!/usr/bin/env python3
"""Demo script to show tmux agent spawning with visual output."""

import time
from pathlib import Path
from cat.agent.tmux import TmuxController

def main():
    print("🚀 Claude Agent Teams - Tmux Demo\n")
    print("=" * 80)

    # Create controller
    controller = TmuxController(session_name="catt-demo")

    # Clean up any existing session
    controller.kill_session()
    print("✓ Cleaned up any existing sessions\n")

    # Create new session
    controller.create_session()
    print("✓ Created tmux session: catt-demo\n")

    # Spawn multiple agents
    agents = [
        ("researcher", "echo '🔍 Researcher Agent Starting...'; sleep 2; echo 'Researching best practices...'", "opus"),
        ("architect", "echo '🏗️  Architect Agent Starting...'; sleep 2; echo 'Designing system architecture...'", "opus"),
        ("developer", "echo '💻 Developer Agent Starting...'; sleep 2; echo 'Writing production code...'", "sonnet"),
        ("tester", "echo '🧪 Tester Agent Starting...'; sleep 2; echo 'Creating test suite...'", "sonnet"),
    ]

    print("📋 Spawning agents in parallel:")
    for role, prompt, model in agents:
        controller.spawn_agent(role, prompt, model)
        print(f"  ✓ Spawned: {role} ({model})")
        time.sleep(0.5)

    print(f"\n✓ All agents spawned!\n")

    # Show tmux windows
    print("🪟 Tmux Windows Created:")
    windows = controller.list_windows()
    for i, window in enumerate(windows, 1):
        print(f"  {i}. {window}")

    print(f"\n{'=' * 80}")
    print("\n📊 Agent Status:\n")

    # Wait a moment for agents to start
    time.sleep(3)

    # Capture output from each agent
    for role, _, model in agents:
        info = controller.get_pane_info(role)
        if info:
            print(f"  {role.upper()} ({model})")
            print(f"    PID: {info['pid']}")
            print(f"    Command: {info['command']}")
            print(f"    Size: {info['width']}x{info['height']}")

        # Capture recent output
        output = controller.capture_output(role, lines=5)
        if output:
            print(f"    Output preview:")
            for line in output.split('\n')[:3]:
                if line.strip():
                    print(f"      {line}")
        print()

    print(f"{'=' * 80}")
    print("\n✨ Demo Complete!\n")
    print("To view the agents in tmux:")
    print(f"  tmux attach -t {controller.session}")
    print("\nTo switch between agents:")
    print("  Ctrl+B, then 'w' to see window list")
    print("  Ctrl+B, then number (0-9) to switch windows")
    print("\nTo detach from tmux:")
    print("  Ctrl+B, then 'd'")
    print("\nTo kill the session:")
    print(f"  tmux kill-session -t {controller.session}")
    print(f"\n{'=' * 80}\n")

    return controller

if __name__ == "__main__":
    controller = main()

    # Keep session alive
    print("Session is running. Press Ctrl+C to cleanup and exit...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🧹 Cleaning up...")
        controller.kill_session()
        print("✓ Session cleaned up. Goodbye!\n")
