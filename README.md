# Claude Agent Teams Framework (CATT)

A CLI wrapper for [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams) — configure and launch coordinated multi-agent teams with a simple YAML config.

> **v2 Architecture (Iteration 6)**: Now uses direct process management instead of tmux. See [ARCHITECTURE-UPDATE.md](ARCHITECTURE-UPDATE.md) for migration details.

## What This Does

CATT simplifies launching Claude Code Agent Teams by:
1. Providing a YAML-based configuration for team structure
2. Generating optimized prompts for team creation
3. Launching Claude Code with the built-in Agent Teams feature

**Note**: This uses Claude Code's native Agent Teams feature (experimental). Enable it in `~/.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## Installation

```bash
# Clone and install
git clone <repo-url>
cd claude-agent-team
pip install -e .

# Requires Claude Code CLI
# Install from: https://claude.ai/code
```

## Quick Start

### 1. Initialize a Project

```bash
cd your-project
catt init                    # Interactive wizard
# Or: catt init --no-interactive

# Edit .catt/project.yaml to customize your team
```

### 2. Preview the Team Prompt

```bash
catt run --dry-run           # Shows the team creation prompt
```

### 3. Launch the Agent Team

```bash
catt run                     # Launches Claude Code with agent team

# Claude will:
# - Create teammates for each role
# - Coordinate work via shared task list
# - Use tmux split panes (or in-process mode)
```

### 4. Interact with Teammates

Once running:
- **Shift+Up/Down**: Switch between teammates
- **Ctrl+T**: View shared task list
- **Shift+Tab**: Toggle delegate mode (lead only coordinates)
- Type directly to message the selected teammate

## CLI Commands

### Initialize (`catt init`)

```bash
catt init                    # Interactive project wizard
catt init --no-interactive   # Create default config
catt init --dir /path/to/project
```

The wizard will ask:
- Project name and description
- Use case (build feature, refactor, research)
- Which agents to enable
- Model selection (opus/sonnet)
- Max iterations per agent

### Run Workflow (`catt run`)

```bash
catt run                     # Start workflow from .catt/project.yaml
catt run --dry-run           # Show execution plan without running
catt run --max-iterations 40 # Limit iterations per agent
catt run --resume            # Resume from saved state
catt run --config custom.yaml
```

### Agent Management (`catt agent`)

```bash
catt agent list              # List all agents and status
catt agent status researcher # Show detailed status for an agent
catt agent logs developer    # View agent output logs
catt agent logs tester -n 100  # Last 100 lines
```

### Chat with Agents (`catt chat`)

```bash
catt chat researcher         # Chat with researcher agent
catt chat manager            # Add context to manager
```

### Dashboard (`catt dashboard`)

```bash
catt dashboard              # Launch Kanban TUI dashboard
catt dashboard --watch      # Auto-refresh on file changes
catt dashboard --multi-agent # Show multi-agent view
```

### Unified Monitor (`catt monitor`) 🆕

```bash
catt monitor                # Launch unified manager
catt monitor --session my-session  # Specify session name
```

**ALL-IN-ONE MONITORING SOLUTION!**
- 🤖 View all active agents (left panel)
- 📺 Live agent output (center panel)
- 📋 Kanban task board (right panel)
- 📊 Real-time statistics (bottom panel)
- ⌨️ Simple keyboard shortcuts (↑/↓ to navigate)
- 🔄 Auto-refresh every 2-5 seconds
- 💬 Send commands directly to agents
- 🎯 Kill/restart agents easily

**Perfect for managing agents + tasks in one unified interface!**

### Tmux Manager (`catt tmux`)

```bash
catt tmux                   # Launch tmux-only manager
catt tmux --session my-session  # Specify session name
```

**Focused tmux monitoring** (use `catt monitor` for full experience):
- 🎨 Beautiful visual interface
- 📺 View live output from agents
- 💬 Send commands directly to agents
- ⌨️ Simple keyboard shortcuts

For managing multiple agents without tmux knowledge.

**Keyboard Shortcuts:**
| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Refresh all panels |
| `↑/↓` | Navigate agents |
| `c` | Focus command input (send to selected agent) |
| `i` | Broadcast message to all agents |
| `Ctrl+K` | Kill selected agent |
| `a` | Attach to raw tmux session |

### Tasks (`catt tasks`)

```bash
catt tasks                  # Show recent tasks (table view)
catt tasks --kanban         # Show tasks in kanban layout
catt tasks --all            # Show all task files
catt tasks --limit 20       # Limit number of files shown
```

### Statistics (`catt stats`)

```bash
catt stats                  # Usage statistics summary
catt stats --daily          # Daily activity breakdown
catt stats --tokens         # Token usage by model
```

### Team Templates (`catt team`)

```bash
catt team list              # List available team templates
catt team spawn dev         # Show spawn prompt for development team
catt team spawn review      # Show spawn prompt for code review team
catt team status            # Show current team activity
```

**Team shortcuts:**
- `dev` → development
- `review` → code-review
- `research` → research
- `manager` → manager-led
- `software` → software-dev

## Interactive Workflow

### 1. Initialize

```
$ catt init

╭─ Claude Agent Teams - Initialize ─────────────────────╮
│                                                       │
│  Project name: my-auth-feature                        │
│  Description: OAuth2 login with Google                │
│                                                       │
│  What do you want to do?                              │
│  > Build a new feature                                │
│                                                       │
│  Select agents to enable:                             │
│  [x] Researcher    (opus)   - Technical research      │
│  [x] Manager       (opus)   - Task coordination       │
│  [x] Architect     (opus)   - System design           │
│  [x] Developer     (sonnet) - Implementation          │
│  [x] Tester        (sonnet) - Test creation           │
│  [x] Reviewer      (sonnet) - Code review             │
│                                                       │
╰───────────────────────────────────────────────────────╯

✓ Config saved to .catt/project.yaml
```

### 2. Run

```
$ catt run

╭─ Project ─────────────────────────────────────────────╮
│ my-auth-feature                                       │
│ OAuth2 login with Google                              │
╰───────────────────────────────────────────────────────╯

Execution Plan:
  1. Researcher (opus)
  2. Manager (opus) (after: researcher)
  3. Architect (opus) (after: manager)
  4. Developer (sonnet) (after: architect)
  5. Tester (sonnet) (after: developer)
  6. Reviewer (sonnet) (after: tester)

→ Started Researcher
```

### 3. Monitor

The dashboard shows agent progress alongside the task kanban:

```
┌─ CATT Dashboard ────────────────────────────────────────────────┐
│ AGENTS              │  TASK KANBAN                              │
│                     │                                           │
│ [>] researcher DONE │   TODO    │  IN PROG  │   DONE           │
│     opus | 5 iter   │  ───────  │  ────────  │  ──────          │
│                     │  Task 1   │  Task 4    │  Task 7          │
│ [ ] manager  RUN    │  Task 2   │  Task 5    │  Task 8          │
│     opus | 12 iter  │  Task 3   │            │  Task 9          │
│                     │           │            │                  │
│ [ ] architect WAIT  │           │            │                  │
│ [ ] developer IDLE  │           │            │                  │
│ [ ] tester    IDLE  │           │            │                  │
│ [ ] reviewer  IDLE  │           │            │                  │
├─────────────────────┴───────────────────────────────────────────┤
│ Progress: [████████░░░░░░░░░░░░] 40% | Agents: 2/6 | Iter: 17  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Configuration

Configuration is stored in `.catt/project.yaml`:

```yaml
name: my-auth-feature
description: OAuth2 login with Google
use_case: build_feature
agents:
  researcher:
    role: researcher
    model: opus
    enabled: true
    depends_on: []
    max_iterations: 40
  manager:
    role: manager
    model: opus
    enabled: true
    depends_on: [researcher]
    max_iterations: 40
  # ... more agents
output_dir: .catt/output
max_total_iterations: 200
```

## Available Teams

| Team | Purpose | Roles |
|------|---------|-------|
| [Code Review](teams/code-review/) | Parallel code review | Security, Performance, Test Coverage |
| [Development](teams/development/) | Feature pipeline | Architect, Implementer, Tester, Reviewer |
| [Research](teams/research/) | Adversarial exploration | Investigator, Devil's Advocate, Synthesizer |
| [Manager-Led](teams/manager-led/) | Coordinated delegation | Manager, Workers |
| [Software Dev](teams/software-dev/) | End-to-end development | PM, Researcher, Architect, Dev, Tester, Reviewer |

## Available Roles

| Role | Focus | Model |
|------|-------|-------|
| [Product Manager](roles/product-manager.md) | Requirements, user stories | opus |
| [Researcher](roles/researcher.md) | Technical evaluation | opus |
| [Architect](roles/architect.md) | Design, interfaces | opus |
| [Manager](roles/manager.md) | Coordination only | opus |
| [Developer](roles/implementer.md) | Production code | sonnet |
| [Tester](roles/tester.md) | Test creation | sonnet |
| [Reviewer](roles/reviewer.md) | Final quality check | sonnet |
| [Security Reviewer](roles/security-reviewer.md) | Vulnerabilities, auth | sonnet |
| [Performance Analyst](roles/performance-analyst.md) | Complexity, queries | sonnet |

## Project Structure

```
claude-agent-team/
├── cat/                       # CLI Application
│   ├── cli.py                 # CLI commands
│   ├── agent/                 # Agent management
│   │   ├── models.py          # Agent data models
│   │   ├── registry.py        # Agent state tracking
│   │   └── tmux.py            # Tmux controller
│   ├── interactive/           # Interactive features
│   │   ├── wizard.py          # Init wizard
│   │   └── config.py          # Project config
│   ├── workflow/              # Workflow engine
│   │   ├── engine.py          # Orchestration
│   │   ├── spawner.py         # Agent spawning
│   │   └── collector.py       # Output collection
│   ├── dashboard/             # Textual TUI
│   │   ├── app.py             # Main application
│   │   ├── kanban.py          # Kanban board
│   │   ├── agent_panel.py     # Agent status panel
│   │   └── chat_panel.py      # Chat interface
│   ├── data/                  # Data layer
│   │   ├── models.py          # Task models
│   │   ├── loader.py          # Data loading
│   │   └── watcher.py         # File watching
│   └── ralph/                 # Ralph loop integration
├── teams/                     # Team templates
├── roles/                     # Role templates
├── settings/                  # Settings
├── docs/                      # Documentation
└── .catt/                     # Project config (created by catt init)
    ├── project.yaml           # Project configuration
    ├── state.json             # Workflow state
    └── output/                # Agent outputs
```

## Key Concepts

### Workflow Dependencies

Agents run in dependency order:
```
Researcher → Manager → Architect → Developer → Tester → Reviewer
```

Each agent waits for its dependencies to complete before starting.

### Model Selection
- **Opus**: Complex reasoning (Research, Manager, Architect)
- **Sonnet**: Efficient execution (Developer, Tester, Reviewer)

### Completion Signals

Each agent outputs a completion signal when done:
- `<promise>RESEARCH_COMPLETE</promise>`
- `<promise>TASKS_CREATED</promise>`
- `<promise>ARCHITECTURE_COMPLETE</promise>`
- etc.

### State Persistence

Workflow state is saved to `.catt/state.json` for resumption:
```bash
catt run --resume  # Continue from where you left off
```

## Requirements

- Python 3.10+
- tmux (required for agent spawning)
- Claude Code with agent teams enabled

```bash
# Install tmux
brew install tmux    # macOS
apt install tmux     # Ubuntu/Debian
```

## Documentation

- [Best Practices](docs/best-practices.md) — Task design, coordination, efficiency
- [Model Selection](docs/model-selection.md) — When to use Opus vs Sonnet
- [Troubleshooting](docs/troubleshooting.md) — Common issues and solutions
- [FAQ](docs/faq.md) — Frequently asked questions
- [Examples](docs/examples.md) — Complete workflow examples

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=cat --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT
