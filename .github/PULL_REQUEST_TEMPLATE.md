<!-- Title in the imperative mood: "Fix ...", "Add ...". It becomes the squash commit subject. -->

## Summary

<!-- What changed and why. Link the issue if there is one: "Closes #123". -->

## How was this tested?

<!-- e.g. new fixture in tests/, ran against a real account (which tools), manual MCP Inspector check -->

## Checklist

- [ ] `uv run pytest` passes
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] Tests added or updated for behaviour changes
- [ ] `CHANGELOG.md` updated under **Unreleased** (if user-visible)
- [ ] No API keys, bearer tokens, user ids, or real health data in the diff
