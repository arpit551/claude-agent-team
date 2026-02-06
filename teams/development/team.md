# Development Team

## Purpose

End-to-end feature development with specialized roles handling architecture, implementation, testing, and review in a coordinated pipeline. Tasks have dependencies ensuring work proceeds in the correct order.

## Team Composition

| Role | Focus | Model | Plan Approval |
|------|-------|-------|---------------|
| Architect | Design, interfaces, patterns | opus | **Required** |
| Implementer | Production code | sonnet | No |
| Tester | Test creation | sonnet | No |
| Reviewer | Final quality check | sonnet | No |

## Workflow

```
┌──────────────┐
│   Architect  │  Task 1: Design architecture
│  (Plan Mode) │  ───────────────────────────
└──────┬───────┘           │
       │ Plan Approved     │
       ▼                   │
┌──────────────┐           │
│ Implementer  │  Task 2: Implement feature (blocked by Task 1)
└──────┬───────┘           │
       │                   │
       ▼                   │
┌──────────────┐           │
│    Tester    │  Task 3: Write tests (blocked by Task 2)
└──────┬───────┘           │
       │                   │
       ▼                   │
┌──────────────┐           │
│   Reviewer   │  Task 4: Final review (blocked by Tasks 2 & 3)
└──────────────┘
```

## Task Dependencies

| Task | Role | Dependencies | Deliverable |
|------|------|--------------|-------------|
| 1. Design | Architect | None | Design document |
| 2. Implement | Implementer | Task 1 | Source code |
| 3. Test | Tester | Task 2 | Test files |
| 4. Review | Reviewer | Tasks 2, 3 | Approval |

## File Ownership

Prevent edit conflicts with clear boundaries:

| Role | Owns | Does Not Touch |
|------|------|----------------|
| Architect | `docs/`, design docs | Source, tests |
| Implementer | `src/features/{{feature}}/` | Tests, docs |
| Tester | `tests/`, `__tests__/` | Source, docs |
| Reviewer | Read-only | Everything |

## Key Configuration

### Delegate Mode
**Recommended** for the lead. Enable with Shift+Tab so the lead coordinates without implementing.

### Plan Approval
**Required** for the Architect role. The design must be approved before implementation begins.

## Best Use Cases

- New feature development
- Module additions
- API endpoint development
- Significant refactors with clear scope

## Anti-patterns (When NOT to Use)

- Bug fixes (use single session)
- Simple enhancements (use single session)
- Exploratory work (use Research team)
- Same-file intensive work (causes conflicts)

## Scaling Options

### Minimal Team (2 roles)
- Architect + Implementer (tester is same as implementer)
- Good for: Small features, prototypes

### Standard Team (4 roles)
- All four roles as described
- Good for: Most feature development

### Extended Team (5+ roles)
- Add multiple implementers for parallel paths
- Add dedicated documentation writer
- Good for: Large features, cross-cutting changes
