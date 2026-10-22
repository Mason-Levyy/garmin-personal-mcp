# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

garmin-personal-mcp is an MCP server that reads a Garmin Connect account from
any MCP client: daily summaries, sleep, HRV, Body Battery, stress, heart rate,
SpO2, weight, nutrition, activities, fitness age, and menstrual cycle data. It
ships to PyPI as `garmin-personal-mcp` and to the MCP Registry, and people run
it against their real accounts.

It is built on Garmin's official
[Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api)
(released October 2026) through Garmin's own client,
[`garmin-connect-personal-api-python`](https://github.com/garmin/connect-personal-api-python).
There is no scraping and no password: the user creates a Personal API key in
Garmin Connect, and the client exchanges it for 24-hour bearer tokens. The
Personal API is read-only and pull-only, so this server never writes to
Garmin. The endpoint reference is the
[Swagger page](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/);
every endpoint on it has a tool.

## Commands

Use uv for everything. `uv.lock` is gitignored, so don't commit one, and don't
`pip install` into the project.

```bash
uv sync                               # install
uv run pytest                         # tests: no network, no Garmin account needed
uv run ruff check .                   # lint (--fix applies safe fixes)
uv run ruff format --check .          # formatting (drop --check to apply)
uv run garmin-personal-mcp auth       # save a real Personal API key
uv run garmin-personal-mcp            # serve over stdio against that account
```

CI runs lint, pytest on Python 3.12 and 3.13, and a version-consistency check.
Run pytest and both ruff commands before pushing.

## Layout

The package is `src/garmin_personal_mcp/`. A tool call flows top to bottom:

- `server.py` defines the MCP tools (`garmin_*`). It parses dates, runs
  blocking work through `fetch`, and shapes the response. Paths and query
  parameters don't go here.
- One module per Garmin feature builds the requests: `daily_summary.py`
  (usersummary-service), `wellness.py` (Body Battery, heart rate, SpO2,
  wellness activities), `sleep.py`, `hrv.py`, `weight.py`, `nutrition.py`,
  `activities.py` (search, detail, workouts, file download), `profile.py`
  (settings, heart rate zones, fitness age), and `womens_health.py`. Each
  function takes the client first. `day.py` composes several of them into the
  one-day overview.
- `garmin_api.py` holds the request plumbing they share: `query` (parameter
  encoding), `in_windows` (splitting long ranges), and `without` (dropping
  sample arrays).
- `garmin_client.py` resolves the key, exchanges it for a bearer token, and
  runs an operation with one retry on 401. `auth.py` is the `auth` command,
  and `config.py` reads env vars and paths.

## Rules that aren't obvious from one file

- **stdout belongs to the MCP protocol.** Under stdio, a `print` anywhere on the
  server path corrupts the stream. Use `logging`, which `cli.py` sends to
  stderr. `print` is fine only in the `auth` command.
- **Every Garmin call from a tool goes through `fetch`.** It runs blocking work
  in a thread through `garmin_client.call`, which retries once with a fresh
  token on a 401, turns Garmin's empty 204 into an explanation, and wraps list
  results in `{"results": [...]}` (a bare empty list reaches the model as no
  content at all). Calling the client directly from a tool skips all of that.
- **Only a 401 means the token went bad.** Missing data comes back as 204 or
  4xx, and `day.get_day` tolerates those per section. A 401 must still
  propagate out of any per-section handling so `call` can retry.
- **Respect Garmin's per-request range limits.** The reference caps steps and
  stress at 28 days, sleep summaries, hydration, and Body Battery at 31, and
  daily summaries at a year. Those endpoints go through `in_windows` so a tool
  accepts any range. Put a newly documented limit next to its endpoint.
- **Keep responses small enough for a model.** All-day sample arrays (heart
  rate, SpO2 single readings, full-resolution Body Battery) are dropped unless
  the caller asks for them. Summaries stay.
- **A model reads the error messages, so make them actionable.** Say what was
  wrong and how to recover. `garmin_client.RECONNECT_HINT`, `parse_range`'s
  swap hint, and `activities.bounding_box` show the pattern. Never blame the
  key for a 5xx.
- **Tool docstrings are the descriptions clients show the model.** They are
  product surface, not comments. When behavior changes, update the argument
  formats, units, defaults, and cross-tool guidance in them to match. Describe
  only fields the Swagger reference documents. Rewording them changes how
  every user's model calls the tools, so treat that as a user-facing change
  too (see below).
- **Dependency pins are deliberate.** `garmin-connect-personal-api-python`
  stays below 2 and `mcp` below 2 until someone has tested a new major against
  a real account.

## Protect existing users

People install this from PyPI and wire it into their MCP clients, prompts, and
scripts. A release that changes what they depend on breaks their setup without
warning. Their public surface is:

- Tool names, parameter names, defaults, and the shape of what tools return.
- CLI commands and flags (`garmin-personal-mcp`, `serve`, `auth`, `--check`,
  `--http`, `--host`, `--port`, `--allowed-host`).
- Environment variables (`GARMIN_PERSONAL_API_KEY`, `GARMIN_MCP_DOWNLOAD_DIR`).
- Where files live and what's in them (the key file and bearer-token cache
  under `~/.config/garmin/`, shared with Garmin's own `gc-personal` CLI).
- Supported Python versions and dependency ranges.

Avoid changing any of these. When a change is needed, make it additive: add a
new optional parameter whose default keeps today's behavior, and keep an old
name working next to its replacement.

When a change will still be felt after an upgrade, flag it. That covers a
breaking change, a new default, a changed return shape, or a renamed or
removed tool. Stop and tell the user before implementing it, and say what
breaks and for whom. In the PR, add a **User impact** section that says what
changes on upgrade and what users need to do. In `CHANGELOG.md`, list it under
**Changed** or **Removed** with the same migration note. This project is
pre-1.0, so a breaking release bumps the minor version.

## Code standards

- **Names over comments.** "Comments" here means comments and docstrings
  alike. Write one only for the *why* that the code can't show, which here is
  usually a Garmin quirk (see `garmin_api.query` and `day.get_day`). Don't
  write comments or docstrings that restate the code, commented-out code,
  changelog notes, or section banners, and delete dead code. Tool docstrings
  are the exception (above).
- **Extract on the second use, not the first.** Don't build abstractions for
  needs that don't exist yet. Once logic appears twice, pull it out and put it
  next to its peers, as `daily_summary.get_stats` does for the three stats
  endpoints.
- **One job per module.** If a module needs "and" to describe it, it should be
  two. A function past about 50 lines wants splitting, and parameters after the
  fourth should be keyword-only (`*`). These are smells to investigate, not hard
  failures. The tool signatures in `server.py` mirror the API and are exempt.
- **Avoid ternaries.** Use a plain `if` instead.
- **Swallowed exceptions are narrow or surfaced.** Never write
  `except Exception: pass`. Catch the specific error and put it in the
  response, as `day.get_day` does.
- **Public functions have type hints.** Garmin-facing functions take the client
  as their first argument and leave it duck-typed, so tests can pass
  `conftest.FakeClient`.
- **New runtime dependencies need a reason.** Every user installs them. Prefer
  the stdlib and what's already in `pyproject.toml`.

## Testing

- The pytest suite lives in `tests/` and never touches the network.
  `conftest.py` provides `FakeClient`, which routes GETs by path fragment and
  answers None (Garmin's 204) for anything unrouted, and points `HOME` at a
  temp directory so no test reads or writes a real key.
- Every behavior change needs a test, and a bug fix needs a test that fails
  without the fix. A new endpoint gets a row in
  `test_endpoints.SINGLE_REQUEST_CASES` or its own test, and response shaping
  ships with a fixture in `tests/fixtures/`.
- Fixtures are synthetic. Scrub display names, user ids, profile pks, tokens,
  and real health data from anything captured from a real account.
- Tests can't prove that a request still works against Garmin. If you couldn't
  try it against a real account, say so in the PR.

## Security

- Never commit or log Personal API keys, bearer tokens, or real health data.
- The key file and token cache are written with mode `0600`, and they stay
  that way.
- Exception messages can reach the MCP client verbatim, so they must never
  include keys or tokens.

## Conventions

- PR and commit titles use the imperative mood and say what changed, e.g. "Add
  hydration windowing for ranges over 31 days". Maintainers squash-merge, so
  the PR title becomes the commit subject.
- User-visible changes get an entry under **Unreleased** in `CHANGELOG.md`.
  Don't create any other new docs unless asked.
- A release bumps `version` in `pyproject.toml` and both version fields in
  `server.json` together, and CI fails if they drift. CONTRIBUTING.md has the
  full steps.
