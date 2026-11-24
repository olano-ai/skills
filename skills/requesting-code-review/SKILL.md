---
name: requesting-code-review
category: engineering
description: Prepare a diff summary and review checklist for an effective code review.
---

# Requesting Code Review

How to prepare and communicate a change for review.

## Before requesting review

- [ ] All tests pass (`make test`)
- [ ] Lint clean (`make check`)
- [ ] Self-reviewed the diff; removed TODOs and debug prints
- [ ] PR description answers: What? Why? How to test?

## Review prompt template

```
## What changed
<one paragraph>

## Why
<motivation / linked issue>

## How to test
1. <step>
2. <step>

## Risk areas
- <files or patterns to scrutinize>
```

## What to ask the reviewer

- Is the approach sound?
- Are there edge cases I missed?
- Is the naming clear?
