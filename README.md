<div align="center">

<img src="https://raw.githubusercontent.com/Mason-Levyy/garmin-personal-mcp/main/assets/logo.png" alt="" width="120">

# Garmin Personal MCP

**Ask your AI about your Garmin data, on Garmin's official API.**

[![Mason-Levyy/garmin-personal-mcp MCP server](https://glama.ai/mcp/servers/Mason-Levyy/garmin-personal-mcp/badges/score.svg)](https://glama.ai/mcp/servers/Mason-Levyy/garmin-personal-mcp)
[![PyPI](https://img.shields.io/pypi/v/garmin-personal-mcp?color=0a64e6)](https://pypi.org/project/garmin-personal-mcp/)
[![CI](https://github.com/Mason-Levyy/garmin-personal-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Mason-Levyy/garmin-personal-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FMason-Levyy%2Fgarmin-personal-mcp%2Fmain%2Fpyproject.toml)](https://github.com/Mason-Levyy/garmin-personal-mcp/blob/main/pyproject.toml)
[![GitHub stars](https://img.shields.io/github/stars/Mason-Levyy/garmin-personal-mcp?style=flat&logo=github)](https://github.com/Mason-Levyy/garmin-personal-mcp/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Mason-Levyy/garmin-personal-mcp/blob/main/LICENSE)

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square&logo=cursor&logoColor=white)](https://cursor.com/en/install-mcp?name=garmin&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJnYXJtaW4tcGVyc29uYWwtbWNwIl19)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522garmin%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522garmin-personal-mcp%2522%255D%257D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect?url=vscode-insiders%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522garmin%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522garmin-personal-mcp%2522%255D%257D)

[Quickstart](#quickstart) · [Tools](#tools) · [Authentication](#authentication) · [Changelog](https://github.com/Mason-Levyy/garmin-personal-mcp/blob/main/CHANGELOG.md)

</div>

Garmin Personal MCP is a free, open-source MCP server that connects your
Garmin Connect account to Claude, Cursor, VS Code, or any other MCP client.
Ask about last night's sleep, HRV trends, Body Battery, stress, training load,
weight, or a specific run, all from your real Garmin account. It runs on
Garmin's official Personal API with a revocable key, so it never needs your
Garmin password, and it's read-only.

Published on PyPI as [`garmin-personal-mcp`](https://pypi.org/project/garmin-personal-mcp/)
and in the official MCP Registry as `io.github.Mason-Levyy/garmin-personal-mcp`.

<!-- mcp-name: io.github.Mason-Levyy/garmin-personal-mcp -->

> **Unofficial project, official API.** This isn't made by Garmin, but it only
> talks to Garmin's documented
> [Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api)
> through [Garmin's own Python client](https://github.com/garmin/connect-personal-api-python).

## How is this different from other Garmin MCP servers?

Most Garmin MCP servers sign in with your Garmin password through the
unofficial `garminconnect` library, which breaks whenever Garmin changes its
login. In October 2026 Garmin opened a Personal
API for individuals. This server uses it:

- **No password, no scraping**: a revocable Personal API key you create in
  Garmin Connect, exchanged for short-lived tokens
- **The whole Personal API**: every working endpoint in Garmin's reference
  has a tool, with every documented filter
- **Any date range**: ranges longer than an endpoint allows (28 days for
  steps, 31 for sleep, and so on) are split into requests for you
- **Model-sized responses**: all-day sample arrays are left out unless you ask
  for them
- **Read-only**: the Personal API can't change your account, and neither can
  this server

## Quickstart

1. Save your Personal API key (one-time; see [Authentication](#authentication)):

   ```bash
   uvx garmin-personal-mcp auth
   ```

2. Add the server to your client. The install buttons at the top do this in
   one click for Cursor and VS Code.

   **Claude Code**

   ```bash
   claude mcp add garmin -- uvx garmin-personal-mcp
   ```

   Or install it as a plugin, which asks for your key in place of step 1:

   ```
   /plugin install garmin-personal-mcp --marketplace Mason-Levyy/garmin-personal-mcp
   ```

   **Claude Desktop** (`claude_desktop_config.json`), **Cursor**
   (`~/.cursor/mcp.json`), **Windsurf** (`~/.codeium/windsurf/mcp_config.json`),
   and **Cline** (`cline_mcp_settings.json`) all take the same entry:

   ```json
   {
     "mcpServers": {
       "garmin": {
         "command": "uvx",
         "args": ["garmin-personal-mcp"]
       }
     }
   }
   ```

   <details>
   <summary><b>VS Code, Codex CLI, Gemini CLI</b></summary>

   VS Code (or use the button above):

   ```bash
   code --add-mcp '{"name":"garmin","command":"uvx","args":["garmin-personal-mcp"]}'
   ```

   Codex CLI:

   ```bash
   codex mcp add garmin -- uvx garmin-personal-mcp
   ```

   Gemini CLI:

   ```bash
   gemini mcp add garmin uvx garmin-personal-mcp
   ```

   </details>

3. Ask it something: *"how did I sleep last night?"*, *"is my HRV trending
   down this month?"*, *"compare my last three long runs"*.

Requires [uv](https://docs.astral.sh/uv/). Any MCP client that speaks stdio or
streamable HTTP works, not just Claude.

> **Finding this useful?** A ⭐ on
> [GitHub](https://github.com/Mason-Levyy/garmin-personal-mcp) helps other
> Garmin users find it.

## Authentication

1. Sign in to Garmin Connect on the web and open
   [Settings → Personal API](https://connect.garmin.com/app/settings/personalApiToken).
2. Create a key and choose how long it lasts (30 days to a year). Garmin shows
   it once.
3. Run `garmin-personal-mcp auth` and paste it at the hidden prompt. The
   server checks it with Garmin before saving it to
   `~/.config/garmin/connect-personal-api-key` with owner-only permissions.

Where there's no terminal to prompt in (a script, or a shell an agent runs),
pipe the key in instead, e.g. `pbpaste | garmin-personal-mcp auth`.

`garmin-personal-mcp auth --check` reports whether the saved key still works,
without prompting. Garmin emails you about a week before a key expires: create
a new one and run `auth` again. No restart is needed; the server reads the key
on every call.

Instead of the key file you can set `GARMIN_PERSONAL_API_KEY`, which takes
precedence. The key file and bearer-token cache are the same ones Garmin's
`gc-personal` CLI uses, so a key saved by either works for both.

## Docker Compose

Run the server as a background HTTP service using the prebuilt image. Save
this as `compose.yaml`:

```yaml
services:
  garmin:
    image: ghcr.io/mason-levyy/garmin-personal-mcp:latest
    command: ["--http", "--host", "0.0.0.0"]
    environment:
      - GARMIN_PERSONAL_API_KEY
    ports:
      - "127.0.0.1:8491:8491"
    volumes:
      - garmin-config:/home/garmin/.config/garmin
      - garmin-downloads:/home/garmin/Downloads/garmin
    restart: unless-stopped

volumes:
  garmin-config:
  garmin-downloads:
```

From the directory containing `compose.yaml`, pull the image:

```bash
docker compose pull
```

### Authentication

Choose **one** of these authentication options:

#### 1. Add your API key to a `.env` file

Create `.env` next to `compose.yaml` and add your Personal API key:

```dotenv
GARMIN_PERSONAL_API_KEY='your-personal-api-key'
```

Compose loads this file automatically. You do not need to run `auth`.

#### 2. Use the interactive `auth` command

Leave `GARMIN_PERSONAL_API_KEY` unset in your shell and `.env`, then run:

```bash
docker compose run --rm garmin auth
```

Paste your Personal API key at the prompt. It is saved for subsequent starts.

### Start the server

```bash
docker compose up -d
```

In your MCP client, add a **Streamable HTTP** server with the URL
`http://127.0.0.1:8491/mcp`. For clients on other machines, see
[Remote / HTTP mode](#remote--http-mode) for VPN and authenticated proxy setup.

### Build from source

Clone the repository and use [compose.yaml](compose.yaml) in its root, which
builds the image from source. From the repository directory, run:

```bash
docker compose build
```

Then follow the authentication and startup steps above. After updating the
source, rebuild and restart with:

```bash
docker compose up --build -d
```

## Tools

All tools take dates as `YYYY-MM-DD`. Range tools default to the 7 days ending
today. Tools that return a list wrap it as `{"results": [...]}`.

| Tool | What it returns |
| --- | --- |
| `garmin_get_day` | One day at a glance: summary, sleep, HRV, Body Battery, stress, and activities |
| `garmin_get_daily_summary` | Every all-day wellness total for one date |
| `garmin_get_daily_summaries` | Daily summaries across a range (trends over weeks or months) |
| `garmin_get_steps` | Daily steps, distance, and goal |
| `garmin_get_stress` | Daily stress level and time in each stress band |
| `garmin_get_hydration` | Daily intake, goal, and sweat loss |
| `garmin_get_body_battery` | Daily charge/drain and the events behind it; `chunks` for intraday lows/highs |
| `garmin_get_heart_rate` | Resting/min/max HR, 7-day resting average, abnormal HR alerts; samples on request |
| `garmin_get_spo2` | Pulse ox averages, hourly averages, acclimation; readings on request |
| `garmin_get_wellness_activities` | Wellness activities with summary values and time in zones |
| `garmin_get_sleep` | One night in full: score, stages, timings, overnight vitals |
| `garmin_get_sleep_summaries` | Nightly sleep records across a range |
| `garmin_get_hrv` | One night of HRV with every reading |
| `garmin_get_hrv_summaries` | Nightly HRV, weekly average, baseline, and status across a range |
| `garmin_get_weight` | Daily weight summaries, range average, and adjacent weigh-ins; every weigh-in with `include_all` |
| `garmin_get_weight_goals` | Weight goals in effect and their target ranges |
| `garmin_get_food_log` | Garmin Connect nutrition log: foods, nutrients, goals, meals |
| `garmin_search_activities` | Activities with every filter Garmin supports (type, dates, distance, power, area, dives, ...) |
| `garmin_get_activity` | One activity in full, with splits |
| `garmin_get_activity_workouts` | The structured workout followed during an activity |
| `garmin_download_activity` | Save an activity's original file (ZIP with the .fit) on the server's machine |
| `garmin_get_profile` | Units, formats, time zone, and training-day preferences |
| `garmin_get_heart_rate_zones` | Zone floors per sport and the HRs they're based on |
| `garmin_get_fitness_age` | Fitness age, achievable fitness age, and its components |
| `garmin_get_menstrual_cycle` | Cycle phase, day, fertile window, and predictions |
| `garmin_get_menstrual_day` | One day's logged symptoms, flow, and cycle detail |

Weights are in grams, distances in meters, and durations in seconds, as Garmin
returns them.

## Remote / HTTP mode

The default transport is stdio. For network clients:

```bash
garmin-personal-mcp --http --host 127.0.0.1 --port 8491
```

This serves streamable HTTP at `/mcp`. **There is no built-in authentication.
Never expose it to the internet.** Bind to localhost and front it with
something that authenticates for you: a VPN or tailnet (e.g. `tailscale
serve`), an authenticating reverse proxy, or an OAuth-aware MCP gateway. Behind
a proxy, pass `--allowed-host <proxy hostname>` (repeatable) so the
DNS-rebinding check accepts its Host header.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `GARMIN_PERSONAL_API_KEY` | Personal API key; overrides the saved key file | – |
| `GARMIN_MCP_DOWNLOAD_DIR` | Where `garmin_download_activity` saves files; the tool can't write outside it | `~/Downloads/garmin` (platform downloads dir) |

## Troubleshooting

- **"Garmin rejected the Personal API key"**: the key expired or was deleted.
  Create a new one and run `garmin-personal-mcp auth`.
- **"No usable Garmin Personal API key was found"**: run `garmin-personal-mcp auth`, or
  set `GARMIN_PERSONAL_API_KEY` in the client config.
- **`{"no_data": ...}`**: Garmin has nothing for that date yet (today's HRV
  before you've slept, for example), or your device doesn't record that
  metric.
- **HTTP 400 on a long range**: an endpoint without a documented limit
  rejected the range. Ask for a shorter one.

## FAQ

**Is this the official Garmin API?** Yes. It uses Garmin's Personal API, which
anyone with a Garmin Connect account can enable without applying, through
Garmin's Apache-licensed Python client. The project itself is independent.

**Can it change my Garmin data?** No. The Personal API is read-only. The one
tool that writes anything, `garmin_download_activity`, saves a file on your
own machine.

**Which MCP clients does it work with?** Any client that runs a stdio or
streamable HTTP server, including Claude Desktop, Claude Code, Cursor,
Windsurf, Cline, and VS Code. AI coding agents can follow
[llms-install.md](https://github.com/Mason-Levyy/garmin-personal-mcp/blob/main/llms-install.md).

**Where does my data go?** The server talks only to Garmin. Your key and
bearer token stay in `~/.config/garmin/`. Tool results go to whichever MCP
client and model you connect it to.

**Can I use it for other people's accounts?** No. Garmin's Personal API is for
your own data. Apps serving other users need Garmin's business developer
program.

## How it works

- `garmin-personal-mcp auth` saves the key; each call exchanges it for a
  bearer token through Garmin's `PersonalApiAuthenticator`, which caches the
  token until an hour before it expires. A token rejected early gets one
  retry with a fresh exchange.
- Each tool maps to one endpoint on `personal.connectapi.garmin.com`
  (`garmin_get_day` combines several). Ranges longer than an endpoint's
  documented maximum are fetched in consecutive windows and concatenated.
- Bulky per-minute sample arrays are dropped by default to keep responses
  readable for a model; `include_samples` or `chunks` bring them back.

## Development

```bash
git clone https://github.com/Mason-Levyy/garmin-personal-mcp
cd garmin-personal-mcp
uv sync
uv run pytest
```

Tests run against synthetic fixtures; no account needed. Lint and formatting
are enforced with `ruff` (`uv run ruff check .`, `uv run ruff format .`).

## Contributing

Issues and pull requests are welcome, especially when Garmin adds endpoints to
the Personal API. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, style, and
the PR checklist, and [SECURITY.md](SECURITY.md) for how to report
vulnerabilities privately. Release history is in [CHANGELOG.md](CHANGELOG.md).

## Support the project

If this server saves you time, please
[star the repo](https://github.com/Mason-Levyy/garmin-personal-mcp). Stars are
how other Garmin users find it in GitHub search and MCP directories. Bug
reports and endpoint requests are just as welcome in
[issues](https://github.com/Mason-Levyy/garmin-personal-mcp/issues).

## License

[MIT](LICENSE). Garmin and Garmin Connect are trademarks of Garmin Ltd. or its
subsidiaries; this project is not affiliated with or endorsed by Garmin.
