# Security Policy

## Scope

This server handles a Garmin Connect Personal API key, which grants read
access to all the health and activity data in the account it belongs to.
Issues in the following areas are in scope:

- Key or token storage, permissions, or leakage (logs, error messages, MCP
  tool output, cache files).
- The HTTP transport (`--http`): anything that weakens the documented
  "localhost-only, no built-in auth" posture.
- `garmin_download_activity` writing outside the directory it was given.
- Dependency vulnerabilities that are reachable through this package.

Out of scope: Garmin's own services and its Personal API.

## Supported versions

Only the latest release on PyPI receives fixes.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's private reporting: go to the repository's **Security** tab and
choose **Report a vulnerability**, or open
<https://github.com/Mason-Levyy/garmin-personal-mcp/security/advisories/new>.

Include what you found, how to reproduce it, and the version affected. You can
expect an acknowledgement within 7 days. Once a fix is released the advisory
will be published with credit to the reporter unless you ask otherwise.

## Handling your own credentials

- Never paste a Personal API key or bearer token into an issue, PR, or test
  fixture.
- The key is stored with owner-only permissions in
  `~/.config/garmin/connect-personal-api-key` (or read from
  `GARMIN_PERSONAL_API_KEY`). If you think it has leaked, delete it on
  [Garmin Connect's Personal API page](https://connect.garmin.com/app/settings/personalApiToken);
  that also invalidates every token issued from it. Then create a new key and
  run `garmin-personal-mcp auth`.
