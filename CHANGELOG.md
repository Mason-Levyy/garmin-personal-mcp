# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- `garmin_download_activity` only saves inside the download folder
  (`GARMIN_MCP_DOWNLOAD_DIR`, else `~/Downloads/garmin`). Its `directory`
  argument now picks a subfolder of it, such as `races`, and a path that leads
  outside it (an absolute path elsewhere, `..`, or a symlink) is rejected, so a
  confused or prompt-injected model can't write files elsewhere on your
  machine. If you saved downloads somewhere else, set
  `GARMIN_MCP_DOWNLOAD_DIR` to that folder.
- The README opens with what the server is, who it's for, and that it's free,
  and the project is called Garmin Personal MCP everywhere, including the MCP
  Registry title (was "Garmin Connect"), so directories and search engines
  show one name.
- `server.json` adds a website link and the logo as an icon, and PyPI gets
  Homepage and Documentation links and more search keywords. These reach the
  Registry and PyPI with the next release.

## [0.1.1] - 2026-10-22

### Added

- A Claude Code plugin in `plugin/`, installable with
  `/plugin install garmin-personal-mcp --marketplace Mason-Levyy/garmin-personal-mcp`.
  It asks for the Personal API key at install, so no `auth` step is needed.
- One-click install buttons for Cursor, VS Code, and VS Code Insiders, and
  setup commands for Codex CLI and Gemini CLI.
- A logo in `assets/`, shown at the top of the README.

### Fixed

- `auth` and `auth --check` say Garmin couldn't be reached, instead of
  crashing with a traceback, when there's no connection or a proxy blocks it.

## [0.1.0] - 2026-10-22

### Added

- First release: an MCP server for Garmin Connect on Garmin's official
  Personal API, with a tool for every working endpoint in Garmin's reference
  (26 tools): daily summaries, steps, stress, hydration, Body Battery, heart
  rate, SpO2, wellness activities, sleep, HRV, weight, weight goals, the
  nutrition log, activity search with every documented filter, activity
  detail, workouts, and file download, profile settings, heart rate zones,
  fitness age, and menstrual cycle data, plus `garmin_get_day` for a one-day
  overview.
- `garmin-personal-mcp auth` saves a Personal API key after checking it with
  Garmin (or reads it from stdin when there's no terminal); `auth --check`
  reports whether the saved key still works.
- Ranges longer than an endpoint's documented limit are split into requests
  automatically.
- All-day sample arrays are left out by default (`include_samples` or `chunks`
  bring them back).
- Streamable HTTP transport (`--http`), with `--allowed-host` for running
  behind a reverse proxy.

[Unreleased]: https://github.com/Mason-Levyy/garmin-personal-mcp/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Mason-Levyy/garmin-personal-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Mason-Levyy/garmin-personal-mcp/releases/tag/v0.1.0
