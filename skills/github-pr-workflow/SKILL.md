---
name: github-pr-workflow
category: workflow
description: End-to-end GitHub PR creation, review, and merge workflow using the built-in git and GitHub tools.
---

# GitHub PR Workflow

Standard process for creating and landing a pull request. Local git runs in
your shell; anything that reaches GitHub goes through the built-in tools,
which use the connected GitHub account — the `gh` command in your sandbox is
not signed in and never will be, so do not use it.

If a GitHub tool answers `[missing-credentials]`, connect the account first
(`magic_link_connect_service("github")`) — never ask for a token in the chat.

## Create

Branch, edit and commit locally with `execute`:

```bash
git checkout -b feat/my-feature
# ... make changes ...
git add <files>
git commit -m "feat: describe the change"
```

Then push with the `git` toolkit (runs outside your sandbox with the
connected account; an owner approves it):

```
git_push(repo_path="<repo path>", set_upstream=True)
```

And open the PR with the GitHub toolkit:

```
github_create_pr(
    repo="owner/repo",
    title="feat: describe",
    head="feat/my-feature",
    base="main",
    body="""## Summary
- What changed and why

## Test plan
- [ ] Tests pass: make test
- [ ] Manual smoke test: <steps>
""",
)
```

## Review

- `github_list_prs(repo="owner/repo")` — find the PR and its number.
- `github_add_pr_comment(repo, number, body)` — leave review notes.

Checklist:

- [ ] CI passes
- [ ] No unintended files in the diff
- [ ] Tests cover the new behavior
- [ ] PR description is clear enough to understand in 6 months

## Merge

```
github_merge_pr(repo="owner/repo", number=<number>, merge_method="squash")
```

Then update your local checkout: `git_fetch(repo_path)` /
`git_pull(repo_path, branch="main")`, and delete the feature branch locally
with `git branch -d feat/my-feature` via `execute`.
