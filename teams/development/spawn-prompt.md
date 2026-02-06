# Development Team - Spawn Prompt

Copy and customize the sections marked with `{{PLACEHOLDER}}`:

---

## Basic Spawn Prompt

```
Create a development team to build {{FEATURE}}.

**Team Structure:**

1. **Architect** (require plan approval): Design the module architecture,
   define interfaces, and document the approach. Focus on {{CONSTRAINTS}}.
   Output a design document before implementation begins.

2. **Implementer**: Write the production code following the architect's
   design. Own files in {{SOURCE_PATH}}. Do not modify test files.

3. **Tester**: Create comprehensive tests after implementation. Own files
   in {{TEST_PATH}}. Cover happy paths, edge cases, and error conditions.

4. **Reviewer**: Review all code after tests pass. Check for standards
   compliance, security issues, and design adherence. Read-only access.

Use Opus for the Architect and Sonnet for others.

Create tasks with dependencies:
- Task 1: Design architecture (Architect)
- Task 2: Implement feature (Implementer, blocked by Task 1)
- Task 3: Write tests (Tester, blocked by Task 2)
- Task 4: Final review (Reviewer, blocked by Tasks 2 and 3)

Enable delegate mode - coordinate only, do not implement directly.

{{CONTEXT}}
```

---

## Customization Points

### FEATURE
What's being built:
- `user authentication system`
- `payment processing module`
- `notification service`
- `dashboard analytics`

### CONSTRAINTS
Architectural priorities:
- `scalability and horizontal scaling`
- `backward compatibility with v1 API`
- `minimal dependencies`
- `real-time performance`

### SOURCE_PATH / TEST_PATH
File ownership:
- Source: `src/features/auth/`, `src/services/payment/`
- Tests: `tests/features/auth/`, `tests/services/payment/`

### CONTEXT
Background:
```
Context:
- Existing patterns: Repository pattern, service layer, DTOs
- Framework: Express with TypeScript
- Database: PostgreSQL with Prisma
- Error handling: Custom AppError class with HTTP codes
```

---

## Variations

### Minimal Team (Architect + Implementer)

```
Create a development team to build {{FEATURE}}.

**Team Structure:**

1. **Architect** (require plan approval): Design the architecture and
   interfaces. Output a design document.

2. **Implementer**: Write production code AND tests following the design.
   Own files in {{SOURCE_PATH}} and {{TEST_PATH}}.

Use Opus for Architect, Sonnet for Implementer.

Tasks:
- Task 1: Design (Architect)
- Task 2: Implement with tests (Implementer, blocked by Task 1)

{{CONTEXT}}
```

### Parallel Implementers

```
Create a development team to build {{FEATURE}}.

**Team Structure:**

1. **Architect** (require plan approval): Design the architecture. Define
   clear boundaries between frontend and backend components.

2. **Frontend Implementer**: Implement UI components. Own {{FRONTEND_PATH}}.

3. **Backend Implementer**: Implement API and services. Own {{BACKEND_PATH}}.

4. **Tester**: Write tests for both frontend and backend. Own {{TEST_PATH}}.

5. **Reviewer**: Final review. Read-only.

Use Opus for Architect, Sonnet for others.

Tasks:
- Task 1: Design (Architect)
- Task 2: Implement frontend (Frontend, blocked by Task 1)
- Task 3: Implement backend (Backend, blocked by Task 1)
- Task 4: Write tests (Tester, blocked by Tasks 2 and 3)
- Task 5: Final review (Reviewer, blocked by Tasks 2, 3, 4)

{{CONTEXT}}
```

---

## Example Complete Prompt

```
Create a development team to build user authentication with JWT.

**Team Structure:**

1. **Architect** (require plan approval): Design the auth module architecture,
   define interfaces for AuthService and TokenService, document the approach.
   Focus on security best practices and session management.
   Output a design document before implementation begins.

2. **Implementer**: Write the production code following the architect's
   design. Own files in src/features/auth/. Do not modify test files.

3. **Tester**: Create comprehensive tests after implementation. Own files
   in tests/features/auth/. Cover happy paths, edge cases, and error conditions.

4. **Reviewer**: Review all code after tests pass. Check for standards
   compliance, security issues, and design adherence. Read-only access.

Use Opus for the Architect and Sonnet for others.

Create tasks with dependencies:
- Task 1: Design authentication architecture (Architect)
- Task 2: Implement auth service and routes (Implementer, blocked by Task 1)
- Task 3: Write auth tests (Tester, blocked by Task 2)
- Task 4: Final security review (Reviewer, blocked by Tasks 2 and 3)

Enable delegate mode - coordinate only, do not implement directly.

Context:
- Express with TypeScript
- PostgreSQL with Prisma for user storage
- Existing patterns: Repository pattern, AppError for errors
- Requirements: JWT in httpOnly cookies, refresh tokens, rate limiting
```
