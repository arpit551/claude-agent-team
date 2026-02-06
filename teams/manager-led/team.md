# Manager-Led Team

## Purpose

Coordinator-driven team where the lead (you) exclusively manages and delegates, never implementing directly. Workers execute tasks under manager guidance with clear ownership boundaries.

## Team Composition

| Role | Focus | Model | Count |
|------|-------|-------|-------|
| Manager (Lead/You) | Coordination, delegation, synthesis | opus | 1 |
| Worker | Task execution | sonnet | 2-6 |

## Key Configuration

### Delegate Mode: REQUIRED

The manager MUST operate in delegate mode:
1. Start the team
2. Press **Shift+Tab** to enable delegate mode
3. Manager can only: spawn teammates, message, manage tasks, synthesize

**Without delegate mode, you may accidentally start implementing instead of coordinating.**

## Workflow

```
                    ┌──────────────┐
                    │   Manager    │
                    │   (You)      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Worker 1 │    │ Worker 2 │    │ Worker 3 │
    │ (Files A)│    │ (Files B)│    │ (Files C)│
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Manager Synth   │
                │ Final Output    │
                └─────────────────┘
```

## Manager Responsibilities

1. **Break down work** into appropriately-sized tasks
2. **Assign tasks** to workers based on complexity
3. **Define file ownership** to prevent conflicts
4. **Monitor progress** and redirect stuck workers
5. **Resolve blockers** and inter-worker conflicts
6. **Synthesize outputs** into final deliverable

## Worker Configuration

### Generalist Workers (Default)
All workers can handle any task type. Assign based on availability.

### Specialized Workers
For larger teams, specialize workers:
- **Frontend Worker**: UI components, styling, client logic
- **Backend Worker**: API, services, data layer
- **Testing Worker**: Tests for all produced code
- **DevOps Worker**: CI/CD, deployment, infrastructure

## Task Sizing Guidelines

| Size | Characteristics | Example |
|------|-----------------|---------|
| Too Small | < 5 min, trivial | "Add a comment" |
| **Optimal** | 15-45 min, clear deliverable | "Implement login form" |
| Too Large | > 2 hours, vague | "Build auth system" |

**Target**: 5-6 optimal-sized tasks per worker

## File Ownership Rules

**Critical**: Prevent edit conflicts with explicit ownership.

```
Worker 1 owns: src/components/
Worker 2 owns: src/api/, src/services/
Worker 3 owns: tests/
```

**Rule**: Workers CANNOT modify files outside their ownership.

## Scaling Guidelines

| Workers | Best For | Overhead |
|---------|----------|----------|
| 2-3 | Simple features, focused work | Low |
| 4-5 | Medium features, parallel streams | Medium |
| 6+ | Large refactors, many files | High |

**Warning**: More workers = more coordination overhead. Start small.

## Best Use Cases

- Large refactoring efforts
- Multi-module features
- Parallel implementation streams
- Work requiring tight coordination

## Anti-patterns (When NOT to Use)

- Tasks a single session could handle
- Highly interdependent work
- Exploratory/research tasks (use Research team)
- Tight deadlines (coordination overhead)
