# 🚀 Quick Start Guide - Claude Agent Teams Framework

## Installation

```bash
# 1. Clone repository
git clone <repo-url>
cd claude-agent-team

# 2. Install dependencies
pip install -e .

# 3. Configure Claude Code
cp settings/settings.json ~/.claude/settings.json
# Enable: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 4. Restart Claude Code
```

## Quick Test (30 seconds)

```bash
# Run comprehensive test suite
python3 test_agent_teams.py

# This spawns 3 projects:
# - auth-team: OAuth2 authentication system
# - api-team: REST API server
# - cli-team: File processing CLI tool
```

## Monitor with Unified UI

```bash
# Launch unified manager for any session
catt monitor --session auth-team
catt monitor --session api-team
catt monitor --session cli-team
```

## UI Layout

```
┌─ Agents ─────────┐┌─ Output ─────────┐┌─ Tasks ─────┐
│ ▶ ✅ researcher  ││ [Live output]    ││ TODO│IN│DONE│
│    (opus)        ││  from selected   ││ ──────────  │
│    Writing tests ││  agent           ││ T1  │T4│ T7 │
│                  ││                  ││ T2  │T5│ T8 │
│ 🔄 developer     ││  Auto-refreshes  ││ T3  │  │    │
│    (sonnet)      ││  every 2s        ││             │
│    Implementing  ││                  ││             │
└──────────────────┘└──────────────────┘└─────────────┘
┌─ Command Input ──────────────────────────────────────┐
│ 💬 [Type command and press Enter...]                │
└──────────────────────────────────────────────────────┘
┌─ Statistics ─────────────────────────────────────────┐
│ 📊 Agents: 3 │ Tasks: 2/2/1 │ Updated: 06:15:23    │
└──────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `↑/↓` | Navigate | Select different agent |
| `c` | Command | Focus input to send command to selected agent |
| `i` | Broadcast | Send command to ALL agents |
| `r` | Refresh | Manually refresh all panels |
| `Ctrl+K` | Kill | Kill selected agent |
| `a` | Attach | Attach to raw tmux session |
| `q` | Quit | Exit unified manager |

## Status Indicators

- ✅ **Done** - Agent completed work
- ❌ **Error** - Agent encountered error
- ⏸️ **Waiting** - Agent is waiting (for dependencies, etc.)
- 💭 **Thinking** - Agent is cogitating/processing
- 🔄 **Running** - Agent actively working

## How to Send Commands

### 1. To Selected Agent
```
1. Press ↑/↓ to select an agent
2. Press 'c' to focus command input
3. Type your command
4. Press Enter
✅ Command sent to selected agent!
```

### 2. To All Agents (Broadcast)
```
1. Press 'i' for broadcast mode
2. Type your command
3. Press Enter
✅ Command sent to ALL agents!
```

## Example Workflow

### Test 1: Authentication System
```bash
# 1. Start test
python3 test_agent_teams.py  # Select option 1

# 2. Monitor
catt monitor --session auth-team

# 3. In UI:
# - See Manager spawn: researcher, architect, developer, tester
# - Watch shared task list populate
# - See agents coordinate via tasks
# - Send commands as needed (press 'c')

# 4. Check results
ls /tmp/test-auth-system/
# Should see: auth.py, config.py, tests/, etc.
```

### Test 2: API Server
```bash
# 1. Start
python3 test_agent_teams.py  # Select option 2

# 2. Monitor
catt monitor --session api-team

# 3. Observe:
# - Manager creates task list
# - Researcher analyzes requirements
# - Architect designs API structure
# - Developer implements endpoints
# - Tester writes tests
# - Reviewer does final check

# 4. Check
ls /tmp/test-api-server/
# Should see: server.py, models.py, tests/, docs/
```

## Verify Agent Teams Integration

### Check Manager Agent
```bash
# In unified UI, select 'manager' agent
# Look for:
- "TaskCreate" tool usage
- "Spawning teammate:" messages
- Shared task list creation
```

### Check Teammate Coordination
```bash
# Select any teammate agent
# Look for:
- Task claiming: [CLAIM] Task #X
- Status updates: [PROGRESS] Task #X - 50%
- Completion: [COMPLETE] Task #X
- Communication: [COORD] @teammate-name
```

## Troubleshooting

### No Agents Visible
```bash
# Check tmux session exists
tmux list-sessions

# If not, run test script
python3 test_agent_teams.py
```

### Agent Not Responding
```bash
# 1. Select agent with ↑/↓
# 2. Check output panel (center) for errors
# 3. If stuck, press Ctrl+K to kill
# 4. Re-spawn if needed
```

### Command Not Sending
```bash
# 1. Ensure agent is selected (▶ marker)
# 2. Press 'c' to focus input
# 3. Type command
# 4. Press Enter
# 5. Check for ✅ confirmation
```

## Best Practices

### 1. Manager-Led Teams
Always start with a Manager agent that:
- Creates shared task list using TaskCreate
- Spawns teammate agents
- Coordinates via task list
- Monitors progress

### 2. Clear Task Definitions
When creating tasks:
- Make them 15-45 minutes each
- Clear deliverables
- Explicit dependencies
- Completion criteria

### 3. File Ownership
Assign clear ownership:
- Researcher: docs/, research.md
- Architect: architecture.md, design/
- Developer: src/, main code
- Tester: tests/, *.test.*

### 4. Model Selection
- Use **Opus** for: Research, Architecture, Management
- Use **Sonnet** for: Development, Testing, Review

## Next Steps

1. ✅ Run test_agent_teams.py
2. ✅ Monitor with unified manager
3. ✅ Try sending commands (press 'c')
4. ✅ Verify Agent Teams coordination
5. ✅ Create your own project with framework

## Resources

- **Agent Teams Docs**: https://code.claude.com/docs/en/agent-teams
- **CLAUDE.md**: Agent Teams guidelines and protocols
- **NEW-FEATURES.md**: Detailed feature documentation
- **END-TO-END-TEST-SUMMARY.md**: Test results and validation

## Support

```bash
# Check help
catt --help
catt monitor --help

# View tasks
catt tasks --kanban

# View statistics
catt stats
```

---

**Ready to build with Claude Agent Teams!** 🚀
