# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/Mason-Levyy/garmin-personal-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Mason-Levyy/garmin-personal-mcp/releases/tag/v0.1.0
