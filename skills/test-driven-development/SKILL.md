---
name: test-driven-development
category: workflow
description: Red-green-refactor TDD loop for building reliable, testable code.
---

# Test-Driven Development

The red-green-refactor loop for writing code that works and stays working.

## The loop

```
1. RED   — write a failing test for one behavior
2. GREEN — write the minimum code to pass the test
3. REFACTOR — clean up; tests must still pass
```

## Rules

- One test at a time
- Never refactor on red
- Keep tests fast (< 1s each)
- Test behavior, not implementation

## Checklist before writing any production code

- [ ] I can state the behavior in one sentence
- [ ] I have a failing test that captures that behavior
- [ ] The test will pass only when the behavior is correct

## Test naming convention

```python
def test_<unit>_<scenario>_<expected_outcome>():
    # arrange
    # act
    # assert
```
