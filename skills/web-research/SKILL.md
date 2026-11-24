---
name: web-research
category: research
description: Fetch, summarize, and cite web content for answering questions.
---

# Web Research

How to reliably research and synthesize information from the web.

## Workflow

1. **Form a search query** — be specific; include version numbers, error codes, or exact terms.
2. **Fetch primary sources** — docs, RFCs, GitHub issues over blog posts.
3. **Cross-reference** — verify claims against ≥2 independent sources.
4. **Summarize** — extract the answer; quote key passages verbatim.
5. **Cite** — always include URLs so the user can verify.

## Output format

```
## Answer
<summary>

## Sources
1. <URL> — <one-line note on why this is authoritative>
2. ...
```

## Caution

- Prefer official docs over tutorials
- Note the publication date; software docs go stale
- Distinguish "works in version X" from "works in latest"
