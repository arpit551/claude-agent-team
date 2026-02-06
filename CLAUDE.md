# Claude Agent Teams Framework

This project provides predefined templates and configurations for Claude Code Agent Teams.

## Quick Start

1. Copy `settings/settings.json` to `~/.claude/settings.json` (or merge with existing)
2. Restart Claude Code
3. Use a spawn prompt from `teams/*/spawn-prompt.md`

## Agent Team Guidelines

When working as part of a team, follow these protocols.

### Communication Protocol

**Report findings to the lead:**
```
[FINDING] Severity: High | File: src/auth.ts:42 | Issue: SQL injection
```

**Coordinate with teammates:**
```
[COORD] @performance-analyst - I found an N+1 query affecting your analysis
```

**Claim tasks:**
```
[CLAIM] Task #3: Implement user validation
```

**Report status:**
```
[PROGRESS] Task #3 - 50% complete, working on password rules
[BLOCKED] Task #3 - Need clarification on requirements
[COMPLETE] Task #3 - Validation implemented, ready for review
```

### File Ownership Rules

Prevent edit conflicts by respecting ownership boundaries:

| Owner | Typical Paths |
|-------|---------------|
| Architect | `docs/`, design documents |
| Frontend | `src/components/`, `src/pages/` |
| Backend | `src/api/`, `src/services/`, `src/models/` |
| Tester | `tests/`, `__tests__/`, `*.test.*` |

**Rule**: Never edit files outside your ownership without lead approval.

### Task Completion Criteria

Mark a task complete only when:
- Code compiles without errors
- All new code has corresponding tests
- Tests pass locally
- No lint errors introduced

### Escalation Protocol

Escalate to the lead when:
- Blocked for more than 10 minutes
- Found a blocker for another teammate
- Found a critical security issue
- Need to modify files outside your ownership

### Model Usage

- **Routine tasks** (implementation, testing): Sonnet
- **Complex decisions** (architecture, research): Opus

## Available Teams

| Team | Use Case | Roles |
|------|----------|-------|
| [Code Review](teams/code-review/) | PR reviews, security audits | Security, Performance, Test Coverage |
| [Development](teams/development/) | Feature development | Architect, Implementer, Tester, Reviewer |
| [Research](teams/research/) | Technology decisions, investigations | Investigator, Devil's Advocate, Synthesizer |
| [Manager-Led](teams/manager-led/) | Large coordinated efforts | Manager, Workers |

## Key Commands

```bash
# Enable agent teams (in settings.json)
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }

# Display modes
teammateMode: "auto" | "in-process" | "tmux"

# Keyboard shortcuts
Shift+Tab     # Toggle delegate mode
Shift+Up/Down # Navigate teammates (in-process mode)
Ctrl+T        # Toggle task list
```

## Best Practices Summary

1. **Task Sizing**: 15-45 minute tasks with clear deliverables
2. **File Ownership**: Assign explicit ownership to prevent conflicts
3. **Model Selection**: Opus for design/research, Sonnet for implementation
4. **Monitoring**: Check in every 15 minutes, redirect early
5. **Dependencies**: Only add where order truly matters
