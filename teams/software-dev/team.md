# Software Development Team

## Purpose

End-to-end software development team covering the complete lifecycle from requirements through deployment. Each role has specialized expertise and clear handoff points.

## Team Composition

| Role | Responsibility | Model | Plan Approval |
|------|----------------|-------|---------------|
| **Product Manager** | Requirements, user stories, acceptance criteria | opus | No |
| **Researcher** | Technical feasibility, library evaluation | opus | No |
| **Architect** | System design, interfaces, patterns | opus | **Required** |
| **Developer** | Production code implementation | sonnet | No |
| **Tester** | Test creation, quality assurance | sonnet | No |
| **Reviewer** | Code review, security check, final approval | sonnet | No |

## Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           Software Development Flow                       │
└──────────────────────────────────────────────────────────────────────────┘

Phase 1: Discovery (Parallel)
┌─────────────────┐     ┌─────────────────┐
│ Product Manager │     │   Researcher    │
│   Requirements  │     │   Feasibility   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
Phase 2: Design
         ┌─────────────────┐
         │    Architect    │
         │  System Design  │
         │ (Plan Approval) │
         └────────┬────────┘
                  │
                  ▼
Phase 3: Implementation
         ┌─────────────────┐
         │    Developer    │
         │  Write Code     │
         └────────┬────────┘
                  │
                  ▼
Phase 4: Quality
         ┌─────────────────┐
         │     Tester      │
         │  Write Tests    │
         └────────┬────────┘
                  │
                  ▼
Phase 5: Approval
         ┌─────────────────┐
         │    Reviewer     │
         │ Final Sign-off  │
         └─────────────────┘
```

## Task Dependencies

| Phase | Task | Role | Blocked By |
|-------|------|------|------------|
| 1 | Gather requirements | PM | None |
| 1 | Research technical options | Researcher | None |
| 2 | Design architecture | Architect | Tasks 1, 2 |
| 3 | Implement feature | Developer | Task 3 |
| 4 | Write tests | Tester | Task 4 |
| 5 | Final review | Reviewer | Tasks 4, 5 |

## File Ownership

| Role | Owns | Does Not Touch |
|------|------|----------------|
| PM | `docs/requirements/`, `*.stories.md` | Code, tests |
| Researcher | `docs/research/`, `docs/adr/` | Code, tests |
| Architect | `docs/design/`, interface definitions | Implementation |
| Developer | `src/` (feature code only) | Tests, docs |
| Tester | `tests/`, `__tests__/`, `*.test.*` | Source code |
| Reviewer | Read-only | Everything |

## Best Use Cases

- New feature development from scratch
- Major module additions
- Greenfield projects
- Features requiring research phase
- Complex integrations

## Anti-patterns (When NOT to Use)

- Bug fixes (use single session)
- Minor enhancements (use Development team)
- Urgent hotfixes (too much overhead)
- Documentation-only changes

## Customization Options

### Skip Research Phase
For well-understood tasks, omit Researcher:
```
Spawn 5 teammates: PM, Architect, Developer, Tester, Reviewer
```

### Add DevOps
For deployment-related features:
```
Add a DevOps Engineer: Handle CI/CD, deployment, infrastructure
Own: .github/, deploy/, Dockerfile, *.yml configs
```

### Parallel Developers
For large features with clear boundaries:
```
- Developer 1 (Frontend): src/components/, src/pages/
- Developer 2 (Backend): src/api/, src/services/
```
