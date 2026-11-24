---
name: writing-plans
category: workflow
description: Author clear implementation plans and technical proposals.
---

# Writing Plans

How to write a plan that is useful to read and easy to execute.

## Structure

```markdown
# Title

> Status: draft | ready | in-progress | done
> Owner: <name>

## Goal
<one sentence>

## Background
<why this work is needed>

## Approach
<ordered list of steps with rationale>

## Out of scope
<explicit non-goals>

## Open questions
- [ ] <question>
```

## Quality checklist

- [ ] Goal is one sentence, not two
- [ ] Steps are sequential and independently testable
- [ ] Non-goals prevent scope creep
- [ ] Someone new could execute the plan without asking questions

## Anti-patterns

- Vague verbs ("improve", "refactor") without specific acceptance criteria
- Missing out-of-scope section — leads to unintended scope creep
- Plan longer than 2 pages — split into phases
