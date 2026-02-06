# Manager-Led Team - Spawn Prompt

Copy and customize the sections marked with `{{PLACEHOLDER}}`:

---

## Basic Spawn Prompt

```
Create a manager-led team to {{OBJECTIVE}}.

I will be the manager. Enable delegate mode immediately - I will coordinate
only and not implement directly.

Spawn {{N}} workers:
{{WORKER_LIST}}

Use Sonnet for all workers.

Break down the work into {{TASK_COUNT}} tasks per worker. Create tasks
with clear deliverables and appropriate dependencies.

File ownership rules:
{{FILE_OWNERSHIP}}

Wait for all workers to complete their tasks before synthesizing the final
result. Do not proceed until explicitly told.

{{CONTEXT}}
```

---

## Customization Points

### OBJECTIVE
What the team will accomplish:
- `refactor the payment module to use the new API`
- `implement the dashboard feature`
- `migrate the database schema to v2`
- `add comprehensive test coverage to src/services/`

### N (Number of Workers)
Recommended: 3-5
- **3 workers**: Most common, good balance
- **4-5 workers**: Larger scope, more parallelism
- **6+ workers**: Only for very large efforts

### WORKER_LIST

**Generalist (Default):**
```
- Worker 1: General purpose, can handle any task
- Worker 2: General purpose, can handle any task
- Worker 3: General purpose, can handle any task
```

**Specialized:**
```
- Worker 1 (Frontend): UI components, styling, client-side logic
- Worker 2 (Backend): API endpoints, services, data layer
- Worker 3 (Testing): Test creation for all produced code
```

### TASK_COUNT
Tasks per worker: 5-6 optimal

### FILE_OWNERSHIP
```
- Worker 1 owns: src/components/, src/pages/
- Worker 2 owns: src/api/, src/services/, src/models/
- Worker 3 owns: tests/, __tests__/
```

### CONTEXT
```
Context:
- Existing codebase uses React + Express + PostgreSQL
- Follow existing patterns in src/features/users/ as reference
- All code must pass ESLint and have 80%+ test coverage
- Do not modify shared utilities in src/lib/
```

---

## Variations

### Specialized Team

```
Create a manager-led team to {{OBJECTIVE}}.

I will be the manager. Enable delegate mode immediately.

Spawn 4 specialized workers:

1. **Frontend Worker**: Handle all UI components and client-side logic.
   Own: src/components/, src/pages/, src/hooks/

2. **Backend Worker**: Handle API and business logic.
   Own: src/api/, src/services/, src/models/

3. **Testing Worker**: Write tests for all produced code.
   Own: tests/, __tests__/, *.test.ts, *.spec.ts

4. **Documentation Worker**: Update docs and API documentation.
   Own: docs/, README.md, API.md

Use Sonnet for all workers.

Tasks should follow this dependency pattern:
- Frontend and Backend work in parallel
- Testing starts after Frontend/Backend complete their modules
- Documentation runs in parallel with Testing

{{CONTEXT}}
```

### Large Refactor

```
Create a manager-led team to refactor {{MODULE}} from {{OLD_PATTERN}} to {{NEW_PATTERN}}.

I will be the manager. Enable delegate mode immediately.

Spawn 5 workers, each owning a subset of files:

- Worker 1 owns: src/{{MODULE}}/components/
- Worker 2 owns: src/{{MODULE}}/services/
- Worker 3 owns: src/{{MODULE}}/api/
- Worker 4 owns: src/{{MODULE}}/models/
- Worker 5 owns: tests/{{MODULE}}/

Use Sonnet for all workers.

Refactoring rules:
- Maintain backward compatibility during migration
- Update imports incrementally
- Each worker completes their area before moving to integration

Create tasks:
1. Workers 1-4: Refactor their owned files (parallel)
2. Worker 5: Update tests after refactoring (blocked by 1-4)
3. All workers: Integration verification (blocked by 5)

{{CONTEXT}}
```

---

## Example Complete Prompt

```
Create a manager-led team to implement the user dashboard feature.

I will be the manager. Enable delegate mode immediately - I will coordinate
only and not implement directly.

Spawn 3 workers:

- Worker 1 (Frontend): Handle dashboard UI components and pages
- Worker 2 (Backend): Handle dashboard API endpoints and services
- Worker 3 (Testing): Write tests for all dashboard code

Use Sonnet for all workers.

File ownership:
- Worker 1 owns: src/components/dashboard/, src/pages/dashboard/
- Worker 2 owns: src/api/dashboard/, src/services/dashboard/
- Worker 3 owns: tests/dashboard/

Break down into these tasks:

Worker 1 (Frontend):
1. Create DashboardLayout component
2. Implement MetricsCard component
3. Implement ActivityFeed component
4. Create DashboardPage with routing

Worker 2 (Backend):
5. Create /api/dashboard/metrics endpoint
6. Create /api/dashboard/activity endpoint
7. Implement DashboardService with caching

Worker 3 (Testing - blocked by tasks 1-7):
8. Write Frontend component tests
9. Write Backend API tests
10. Write integration tests

Wait for all workers to complete their tasks before synthesizing.

Context:
- React with TypeScript for frontend
- Express with TypeScript for backend
- Jest for testing
- Follow patterns in src/features/users/ as reference
- Use Recharts for data visualization
```

---

## Manager Checklist

Use this during the session:

### Startup
- [ ] Enable delegate mode (Shift+Tab)
- [ ] Verify all workers spawned
- [ ] Confirm file ownership is understood
- [ ] Task list created (Ctrl+T to view)

### During Execution
- [ ] Check progress every 15 minutes
- [ ] Message stuck workers for status
- [ ] Reassign blocked tasks if needed
- [ ] Resolve inter-worker questions

### Completion
- [ ] All tasks marked complete
- [ ] Collect outputs from all workers
- [ ] Synthesize final deliverable
- [ ] Clean up team: "Clean up the team"
