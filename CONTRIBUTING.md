# Contributing to garmin-personal-mcp

Thanks for your interest. This project wraps Garmin's official Personal API,
so the most valuable contributions keep it in step with that API as Garmin
adds endpoints and fields. Bug reports, response captures, and pull requests
are all welcome.

## Ground rules

- Be respectful. See the [Code of Conduct](CODE_OF_CONDUCT.md).
- **Never commit credentials.** No Personal API keys, bearer tokens, or real
  health data in fixtures. See [SECURITY.md](SECURITY.md).
- Open an issue before starting large changes (new tools, transport changes,
  auth rework) so we can agree on the approach first.
- Small, focused pull requests are easier to review and land faster.

## Development setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone https://github.com/Mason-Levyy/garmin-personal-mcp
cd garmin-personal-mcp
uv sync
uv run pre-commit install    # optional: runs lint/format on every commit
```

Run the same checks CI runs:

```bash
uv run pytest                 # tests (synthetic fixtures, no Garmin account needed)
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
```

`uv run ruff format .` fixes formatting; `uv run ruff check --fix .` applies
safe lint fixes.

To exercise the server against a real account, follow the
[Authentication](README.md#authentication) steps in the README and run
`uv run garmin-personal-mcp`. Point an MCP client at it, or use the
[MCP Inspector](https://github.com/modelcontextprotocol/inspector).

## Project layout

| Path | Purpose |
| --- | --- |
| `src/garmin_personal_mcp/server.py` | MCP tool definitions (`garmin_*`) |
| `src/garmin_personal_mcp/day.py` | The one-day overview built from several endpoints |
| `src/garmin_personal_mcp/daily_summary.py`, `wellness.py`, `sleep.py`, `hrv.py`, `weight.py`, `nutrition.py`, `activities.py`, `profile.py`, `womens_health.py` | One module per Garmin feature |
| `src/garmin_personal_mcp/garmin_api.py` | Request plumbing shared by the feature modules |
| `src/garmin_personal_mcp/garmin_client.py` | Key resolution, token exchange, and the 401 retry |
| `src/garmin_personal_mcp/auth.py` | The `auth` command |
| `src/garmin_personal_mcp/config.py` | Env vars and paths |
| `src/garmin_personal_mcp/cli.py` | `garmin-personal-mcp` entry point |
| `tests/` | Pytest suite with synthetic JSON fixtures |

## Making changes

1. Fork the repo and create a branch from `main`
   (`fix/short-description`, `feat/short-description`, `docs/...`, `chore/...`).
2. Make your change. Add or update tests for any behaviour change; new
   endpoints get a row in `tests/test_endpoints.py`, and response shaping
   ships with a fixture in `tests/fixtures/`.
3. Keep fixtures synthetic. Scrub display names, ids, and real health data from
   anything captured from your own account.
4. Run `pytest`, `ruff check`, and `ruff format --check` locally.
5. Update `CHANGELOG.md` under **Unreleased** if the change is user-visible.
6. Open a pull request against `main`. Fill in the template and link any
   related issue.

### Pull request requirements

`main` is protected. A pull request can be merged only when:

- CI is green (tests on Python 3.12 and 3.13, lint, version consistency).
- All review conversations are resolved.

Maintainers squash-merge by default; keep the PR title in the style below
because it becomes the commit subject.

### Commit and PR titles

Use the imperative mood and say what changed, not how:

```
Add hydration windowing for ranges over 31 days
Fix activity search dropping the subtype filter
```

### Code style

- Formatting and linting are enforced by [ruff](https://docs.astral.sh/ruff/);
  configuration lives in `pyproject.toml`.
- Prefer descriptive names over comments. Comment only where the *why* is not
  obvious (for example, a Garmin quirk being worked around).
- Type hints on public functions. Tests are the exception; keep them readable.
- Match the surrounding code's idiom rather than introducing new patterns.

## When Garmin changes the API

Garmin publishes the Personal API reference as a
[Swagger page](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/).
If an endpoint, parameter, or range limit appears there that this server
doesn't cover, an issue or PR quoting the reference entry is the most useful
contribution. When sharing a real response, **redact** your display name,
profile pk, ids, and personal data first.

## Releasing (maintainers)

Releases are cut automatically. Bump `version` in `pyproject.toml` **and** the
two version fields in `server.json` (CI fails if they drift), move the
**Unreleased** section of `CHANGELOG.md` under the new version, and merge to
`main`. The publish workflow tags `vX.Y.Z`, creates a GitHub release, publishes
to PyPI via trusted publishing, and pushes to the MCP Registry.

## License

By contributing you agree that your contributions are licensed under the
[MIT License](LICENSE).
