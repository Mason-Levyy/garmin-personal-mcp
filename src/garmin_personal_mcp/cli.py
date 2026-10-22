import argparse
import logging
import sys

from mcp.server.transport_security import TransportSecuritySettings

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
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

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
