# Model Selection Guide

## Overview

Agent teams support mixing models across teammates. Use this guide to optimize for capability vs. cost.

## Model Characteristics

| Model | Strengths | Cost | Best For |
|-------|-----------|------|----------|
| **opus** | Deepest reasoning, complex analysis, nuanced judgment | Highest | Architecture, research, complex debugging |
| **sonnet** | Fast, efficient, good at patterns, high throughput | Medium | Implementation, testing, routine review |

## Role-Based Recommendations

### Architecture Roles
**Recommended**: opus

- Design decisions have long-term impact
- Requires understanding trade-offs
- Benefits from deeper reasoning
- Can consider more alternatives

### Research Roles
**Recommended**: opus

- Hypothesis generation requires creativity
- Adversarial analysis needs nuanced reasoning
- Synthesis requires broad understanding
- Better at identifying non-obvious connections

### Implementation Roles
**Recommended**: sonnet

- Following established patterns
- Translating designs to code
- High throughput, lower complexity
- Pattern matching is sufficient

### Testing Roles
**Recommended**: sonnet

- Systematic test generation
- Pattern-based coverage analysis
- Edge case enumeration
- Follows established test patterns

### Review Roles
**Recommended**: sonnet (routine) or opus (security)

- Style/standards checking: Sonnet
- Security vulnerability analysis: Opus
- Performance deep-dives: Opus
- Routine code review: Sonnet

---

## Team Configurations by Budget

### Cost-Optimized
All teammates use sonnet.

**Best for:**
- Well-defined tasks
- Established patterns
- Routine work
- Tight budgets

**Example:**
```
Use Sonnet for all teammates.
```

### Balanced (Recommended)
Lead + complex roles use opus, others use sonnet.

**Best for:**
- New feature development
- Moderate complexity
- Most common scenarios

**Example:**
```
Use Opus for the Architect and Sonnet for the Implementer, Tester, and Reviewer.
```

### Capability-Optimized
All teammates use opus.

**Best for:**
- Research and exploration
- Complex debugging
- Critical security analysis
- Novel problems

**Example:**
```
Use Opus for all teammates (research requires deep reasoning).
```

---

## Decision Matrix

| Factor | Favor Opus | Favor Sonnet |
|--------|------------|--------------|
| Task novelty | Novel, first-time | Routine, repeatable |
| Decision impact | Long-term, architectural | Short-term, local |
| Reasoning depth | Multi-step, nuanced | Pattern matching |
| Error tolerance | Low (security, data) | Higher (can iterate) |
| Speed requirement | Can wait for quality | Need fast throughput |
| Budget constraint | Flexible | Tight |

---

## Spawn Prompt Examples

### Specifying Model
```
Spawn an architect teammate using Opus. ...
```

### Mixed Models
```
Create a development team. Use Opus for the Architect and Sonnet for
the Implementer and Tester.
```

### All Same Model
```
Use Sonnet for all reviewers.
```

```
Use Opus for all teammates (research requires deep reasoning).
```

---

## Cost Estimation

Agent teams use more tokens than single sessions because:
1. Each teammate has its own context window
2. Communication adds overhead
3. Coordination requires extra messages

**Rough multiplier**:
- 3-teammate team ≈ 4-5x single session tokens
- 5-teammate team ≈ 7-8x single session tokens

**Cost reduction strategies:**
1. Use Sonnet for most roles
2. Start with fewer teammates
3. Scope tasks tightly
4. Monitor and redirect early
