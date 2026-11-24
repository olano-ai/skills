---
name: plan
category: workflow
description: Structured planning and TDD workflow for non-trivial tasks.
---

# Plan

Use this skill to break down complex tasks into a clear, testable plan before writing any code.

## When to invoke

- Task has more than 3 steps
- Task touches multiple modules
- You are unsure where to start

## Workflow

1. **Understand** — restate the goal in your own words; list constraints.
2. **Decompose** — break into atomic sub-tasks; order by dependency.
3. **Write tests first** — sketch assertions before implementation.
4. **Implement** — one sub-task at a time; mark done before moving on.
5. **Verify** — run tests; confirm the plan is fully executed.

## Output format

```
Goal: <one sentence>
Constraints: <list>
Steps:
  [ ] 1. <step>
  [ ] 2. <step>
  ...
```
