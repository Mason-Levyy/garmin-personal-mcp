# Installing garmin-personal-mcp (for AI coding agents)

These steps install the Garmin Connect MCP server for Cline, Claude Code,
Cursor, or any other MCP client. The package is `garmin-personal-mcp` on PyPI
and runs with `uvx`.

## 1. Check for uv

```bash
uvx --version
```

If that fails, install uv (https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.

## 2. Have the user save their key

Authentication needs a Garmin Connect Personal API key, pasted at a hidden
prompt. Don't ask the user to paste the key into chat. Ask them to create one
at https://connect.garmin.com/app/settings/personalApiToken (Garmin shows it
once) and then run this in their own terminal:

```bash
uvx garmin-personal-mcp auth
```

The key is saved to `~/.config/garmin/connect-personal-api-key`, so the server
config needs no secrets.

To confirm it worked (no prompt, safe to run yourself):

```bash
uvx garmin-personal-mcp auth --check
```

## 3. Add the server to the client

Server name: `garmin`. Command: `uvx`. Args: `["garmin-personal-mcp"]`.
Transport: stdio.

Claude Code:

```bash
claude mcp add garmin -- uvx garmin-personal-mcp
```

Cline (`cline_mcp_settings.json`), Cursor (`~/.cursor/mcp.json`), Claude Desktop
(`claude_desktop_config.json`), and Windsurf (`~/.codeium/windsurf/mcp_config.json`)
all take the same entry:

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

Restart or reload the client afterwards.

## 4. Verify

Call `garmin_get_day` with no arguments. It returns today's overview. An error
mentioning `garmin-personal-mcp auth` means step 2 didn't complete: run
`uvx garmin-personal-mcp auth --check` and have the user re-run
`uvx garmin-personal-mcp auth`.

## Optional environment variables

- `GARMIN_PERSONAL_API_KEY`: the key itself, instead of the saved file. Mark it
  secret in the client config.
- `GARMIN_MCP_DOWNLOAD_DIR`: where `garmin_download_activity` saves files
  (default `~/Downloads/garmin`). The tool can't write outside this folder; its
  `directory` argument only picks a subfolder. If the user wants downloads
  somewhere else, set this variable rather than passing an outside path.
