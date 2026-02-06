#!/usr/bin/env python3
"""
Test script to create real projects using Claude Agent Teams.
This tests the framework end-to-end with actual agent coordination.
"""

import sys
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cat.agent.tmux import TmuxController


def test_auth_system_project():
    """Test 1: Build an authentication system."""
    print("=" * 70)
    print("TEST 1: Authentication System with Agent Teams")
    print("=" * 70)
    print()

    project_dir = Path("/tmp/test-auth-system")
    project_dir.mkdir(exist_ok=True)

    controller = TmuxController(session_name="auth-team")
    controller.kill_session()
    controller.create_session()

    print("📋 Project: OAuth2 Authentication System")
    print("📁 Directory:", project_dir)
    print()

    # Spawn manager agent (coordinates the team)
    print("👔 Spawning Manager agent (opus)...")
    controller.spawn_agent(
        "manager",
        """You are the Manager agent coordinating an authentication system project.

Your role:
1. Create a shared task list using TaskCreate
2. Spawn teammate agents: researcher, architect, developer, tester
3. Coordinate their work - they should use the shared task list
4. Monitor progress and provide guidance

Project Goal: Build an OAuth2 authentication system with Google login

Create these tasks:
- Research OAuth2 best practices and security considerations
- Design authentication system architecture
- Implement OAuth2 flow with Google provider
- Write comprehensive tests

Use Claude Agent Teams properly - spawn teammates and coordinate via shared task list.
Output <promise>TEAM_COORDINATED</promise> when all agents are working.""",
        "opus",
        working_dir=project_dir
    )
    time.sleep(3)

    print("✅ Manager agent spawned")
    print()
    print("🎯 Manager will spawn and coordinate the team...")
    print("   - Researcher (opus): Technical research")
    print("   - Architect (opus): System design")
    print("   - Developer (sonnet): Implementation")
    print("   - Tester (sonnet): Test creation")
    print()
    print(f"📺 Monitor: catt monitor --session auth-team")
    print()

    return "auth-team", project_dir


def test_api_server_project():
    """Test 2: Build a REST API server."""
    print("=" * 70)
    print("TEST 2: REST API Server with Agent Teams")
    print("=" * 70)
    print()

    project_dir = Path("/tmp/test-api-server")
    project_dir.mkdir(exist_ok=True)

    controller = TmuxController(session_name="api-team")
    controller.kill_session()
    controller.create_session()

    print("📋 Project: REST API Server with Database")
    print("📁 Directory:", project_dir)
    print()

    # Spawn manager agent
    print("👔 Spawning Manager agent (opus)...")
    controller.spawn_agent(
        "manager",
        """You are the Manager agent coordinating an API server project.

Your role:
1. Create a shared task list using TaskCreate
2. Spawn teammate agents: researcher, architect, developer, tester, reviewer
3. Coordinate their work via shared task list
4. Ensure proper sequencing (research → architecture → development → testing → review)

Project Goal: Build a REST API server with:
- User CRUD endpoints
- PostgreSQL database
- Input validation
- Error handling
- API documentation

Create appropriate tasks for each agent.
Use Claude Agent Teams - spawn teammates and use shared task list for coordination.
Output <promise>TEAM_COORDINATED</promise> when all agents are working.""",
        "opus",
        working_dir=project_dir
    )
    time.sleep(3)

    print("✅ Manager agent spawned")
    print()
    print(f"📺 Monitor: catt monitor --session api-team")
    print()

    return "api-team", project_dir


def test_cli_tool_project():
    """Test 3: Build a CLI tool."""
    print("=" * 70)
    print("TEST 3: CLI Tool with Agent Teams")
    print("=" * 70)
    print()

    project_dir = Path("/tmp/test-cli-tool")
    project_dir.mkdir(exist_ok=True)

    controller = TmuxController(session_name="cli-team")
    controller.kill_session()
    controller.create_session()

    print("📋 Project: File Processing CLI Tool")
    print("📁 Directory:", project_dir)
    print()

    # Spawn manager agent
    print("👔 Spawning Manager agent (opus)...")
    controller.spawn_agent(
        "manager",
        """You are the Manager agent coordinating a CLI tool project.

Your role:
1. Create shared task list using TaskCreate
2. Spawn teammates: product_manager, researcher, developer, tester
3. Coordinate work via shared task list
4. Monitor and guide the team

Project Goal: Build a CLI tool that:
- Processes text files (count words, lines, characters)
- Supports multiple input files
- Has colorful output
- Includes --help and --version flags

Create tasks for:
- Product requirements (PM)
- Technical research (Researcher)
- Implementation (Developer)
- Testing (Tester)

Use Claude Agent Teams properly with shared task list coordination.
Output <promise>TEAM_COORDINATED</promise> when team is working.""",
        "opus",
        working_dir=project_dir
    )
    time.sleep(3)

    print("✅ Manager agent spawned")
    print()
    print(f"📺 Monitor: catt monitor --session cli-team")
    print()

    return "cli-team", project_dir


def show_all_sessions():
    """Show all active test sessions."""
    print()
    print("=" * 70)
    print("📊 ACTIVE TEST SESSIONS")
    print("=" * 70)
    print()

    sessions = ["auth-team", "api-team", "cli-team"]

    for session in sessions:
        result = subprocess.run(
            ["tmux", "list-windows", "-t", session, "-F", "#{window_name}"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            windows = result.stdout.strip().split('\n')
            agents = [w for w in windows if w and w != 'main']
            print(f"🎯 {session}:")
            print(f"   Agents: {', '.join(agents) if agents else 'No agents yet'}")
            print()

    print("📺 Monitor any session:")
    print(f"   catt monitor --session auth-team")
    print(f"   catt monitor --session api-team")
    print(f"   catt monitor --session cli-team")
    print()


def main():
    """Run all test projects."""
    print()
    print("🚀 TESTING CLAUDE AGENT TEAMS FRAMEWORK")
    print("=" * 70)
    print()
    print("This will test the framework with 3 real projects:")
    print("  1. OAuth2 Authentication System")
    print("  2. REST API Server")
    print("  3. CLI File Processing Tool")
    print()
    print("Each project uses a Manager agent that spawns and coordinates")
    print("a team using Claude Code's Agent Teams feature.")
    print()
    input("Press Enter to start tests...")
    print()

    # Run test 1
    test_auth_system_project()
    time.sleep(2)

    # Run test 2
    test_api_server_project()
    time.sleep(2)

    # Run test 3
    test_cli_tool_project()
    time.sleep(2)

    # Show summary
    show_all_sessions()

    print("=" * 70)
    print("✅ ALL TEST PROJECTS SPAWNED")
    print("=" * 70)
    print()
    print("Monitor with:")
    print("  catt monitor --session auth-team")
    print("  catt monitor --session api-team")
    print("  catt monitor --session cli-team")
    print()
    print("The manager agents will:")
    print("  1. Create shared task lists")
    print("  2. Spawn teammate agents")
    print("  3. Coordinate work via task lists")
    print("  4. Monitor progress")
    print()
    print("Wait ~5-10 minutes for agents to complete their work.")
    print()


if __name__ == "__main__":
    main()
