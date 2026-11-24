---
name: systematic-debugging
category: engineering
description: Step-by-step debugging recipe for isolating and fixing bugs.
---

# Systematic Debugging

A reliable process for diagnosing bugs without guessing.

## Steps

1. **Reproduce** — find the smallest input that triggers the bug; add a failing test.
2. **Locate** — identify the layer (data, logic, I/O, integration).
3. **Hypothesize** — form one specific hypothesis; state what you expect to be true.
4. **Inspect** — read relevant code; add targeted logging or breakpoints.
5. **Verify hypothesis** — run the failing test; check whether evidence matches.
6. **Fix** — minimal change that makes the test pass.
7. **Confirm no regression** — run the full test suite.

## Anti-patterns to avoid

- Changing multiple things at once
- Skipping step 1 (not having a reproducible case)
- Editing code before reading it
