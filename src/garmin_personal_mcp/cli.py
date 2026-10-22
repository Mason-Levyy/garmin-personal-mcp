import argparse
import logging
import sys

from mcp.server.transport_security import TransportSecuritySettings

from . import __version__

LOOPBACK_HOSTS = ["127.0.0.1", "localhost"]


def transport_security(extra_hosts: list[str]) -> TransportSecuritySettings:
    hosts = LOOPBACK_HOSTS + extra_hosts
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts + [f"{host}:*" for host in hosts],
        allowed_origins=[
            f"{scheme}://{host}{port}"
            for scheme in ("http", "https")
            for host in hosts
            for port in ("", ":*")
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="garmin-personal-mcp",
        description="MCP server for the Garmin Connect Personal API (stdio by default).",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["serve", "auth"],
        default="serve",
        help="serve (default) or auth to save your Garmin Personal API key",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="with auth: report whether the saved key works, without prompting",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="serve over streamable HTTP instead of stdio",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="HTTP bind host (default 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8491, help="HTTP port (default 8491)"
    )
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help="extra Host header to accept over HTTP, e.g. a reverse proxy's hostname",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()

    if args.check and args.command != "auth":
        parser.error("--check only applies to the auth command")

    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    if args.command == "auth":
        from .auth import run_auth_flow, run_check

        if args.check:
            raise SystemExit(run_check())
        raise SystemExit(run_auth_flow())

    from .server import mcp

    if not args.http:
        mcp.run()
        return
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.settings.transport_security = transport_security(args.allowed_host)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
