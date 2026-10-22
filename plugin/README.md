# Garmin Personal MCP plugin

This plugin connects Claude to your Garmin Connect account through
[garmin-personal-mcp](https://github.com/Mason-Levyy/garmin-personal-mcp), an
open-source MCP server built on Garmin's official
[Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api).
Ask about last night's sleep, HRV trends, Body Battery, stress, training load,
weight, or a specific run.

## Install

In Claude Code:

```
/plugin install garmin-personal-mcp --marketplace Mason-Levyy/garmin-personal-mcp
```

## What it needs

- [uv](https://docs.astral.sh/uv/) on your machine. The plugin runs the
  server with `uvx`, which downloads the pinned `garmin-personal-mcp` release
  from PyPI the first time it starts.
- A Garmin Personal API key. Create one in Garmin Connect under
  [Settings, Personal API](https://connect.garmin.com/app/settings/personalApiToken)
  and paste it when the plugin asks. It is stored as a sensitive setting and
  passed to the server as `GARMIN_PERSONAL_API_KEY`.

## What it runs and sends

The server runs locally over stdio. It talks only to Garmin's Personal API at
`personal.connectapi.garmin.com`, which exchanges your key for a short-lived
token and returns your data. The Personal API is
read-only, so nothing in your Garmin account can be changed. The one tool that
writes anything, `garmin_download_activity`, saves an activity file to your
own downloads folder. Tool results go to the Claude session you use them in.

When your key expires, create a new one in Garmin Connect and update the
plugin's setting.

Not affiliated with or endorsed by Garmin. Licensed under MIT.
