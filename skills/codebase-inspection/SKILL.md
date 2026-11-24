---
name: codebase-inspection
category: engineering
description: Systematic repo map and symbol lookup for understanding an unfamiliar codebase.
---

# Codebase Inspection

A structured approach for orienting yourself in an unfamiliar repository.

## Entry-point discovery

1. Read `README.md` / `CLAUDE.md` / `pyproject.toml` for the project overview and commands.
2. Find the main CLI entry (`pyproject.toml [project.scripts]` or `__main__.py`).
3. Trace the top-level data flow from CLI → core → persistence.

## Symbol lookup workflow

```
grep -r "SymbolName" src/ --include="*.py" -l   # which files
grep -n "def SymbolName\|class SymbolName" src/  # definition
grep -rn "SymbolName" src/ | grep -v test        # callers
```

## Architecture map checklist

- [ ] Entry points
- [ ] Config / settings model
- [ ] Core data model (dataclass / Pydantic model)
- [ ] Persistence layer (DB, files, cache)
- [ ] External integrations (HTTP, queue, LLM)
- [ ] Test fixtures / mocks
