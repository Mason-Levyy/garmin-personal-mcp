# garmin-personal-mcp

A read-only MCP server for your own Garmin Connect data, built on Garmin's
official [Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api)
and its [Python client](https://github.com/garmin/connect-personal-api-python).
No password, no scraping: you create a Personal API key in Garmin Connect and
the server exchanges it for 24-hour bearer tokens as needed.

## Setup

1. In Garmin Connect, open
   [Settings → Personal API](https://connect.garmin.com/app/settings/personalApiToken)
   and create a key. Garmin shows it once.
2. Save it where the server looks for it:

   ```bash
   mkdir -p ~/.config/garmin
   install -m 600 /dev/stdin ~/.config/garmin/connect-personal-api-key <<< 'YOUR-KEY'
   ```

   Or set `GARMIN_PERSONAL_API_KEY`. Keys expire after the period you chose
   (30 days to a year); Garmin emails a week before. Replace the file with the
   new key and the server picks it up on the next call.
3. Run it:

   ```bash
   uvx garmin-personal-mcp                 # stdio
   uvx garmin-personal-mcp --http          # streamable HTTP on 127.0.0.1:8491/mcp
   ```

   Behind a reverse proxy, add `--allowed-host <proxy hostname>` so the
   DNS-rebinding check accepts its Host header.

## Tools

All tools are read-only. Dates are `YYYY-MM-DD`; ranges default to the 7 days
ending today.

| Tool | Returns |
|---|---|
| `garmin_get_day` | Summary, sleep, HRV, body battery, stress, and activities for one day |
| `garmin_daily_summaries` | Per-day totals over a range |
| `garmin_sleep` / `garmin_sleep_summaries` | One night in full / nightly summaries |
| `garmin_hrv` | Overnight HRV, baseline, and status |
| `garmin_body_battery`, `garmin_stress`, `garmin_steps` | Daily series |
| `garmin_heart_rate` | One day's resting/min/max HR and samples |
| `garmin_weight` | Weigh-ins and body composition |
| `garmin_activities` / `garmin_activity` | Activity list / one activity in full |
| `garmin_profile` | Profile settings and HR zones |
| `garmin_get` | Any other Personal API GET path |

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```
