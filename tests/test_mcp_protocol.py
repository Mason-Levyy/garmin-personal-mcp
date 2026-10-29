import asyncio
import json
import sys

from conftest import FakeClient, http_error
from mcp import Client, StdioServerParameters
from mcp.server.mcpserver import MCPServer
from starlette.testclient import TestClient

from garmin_personal_mcp import cli, garmin_client, server


def test_stdio_lists_tools_and_returns_input_errors():
    async def exercise():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "garmin_personal_mcp.cli"]
        )
        async with Client(params) as client:
            tools = (await client.list_tools()).tools
            assert len(tools) == 26
            for tool in tools:
                annotations = tool.annotations
                assert annotations.open_world_hint is True
                if tool.name == "garmin_download_activity":
                    assert annotations.read_only_hint is False
                    assert annotations.destructive_hint is False
                    assert annotations.idempotent_hint is True
                else:
                    assert annotations.read_only_hint is True

            result = await client.call_tool(
                "garmin_get_steps", {"start": "2026-01-02", "end": "2026-01-01"}
            )
            assert result.is_error
            assert (
                "start (2026-01-02) must be on or before end (2026-01-01); swap them"
                in result.content[0].text
            )

    asyncio.run(exercise())


def test_http_rejects_unapproved_hosts():
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1"},
        },
    }
    headers = {"accept": "application/json, text/event-stream"}
    for extra_hosts in ([], ["example.test"]):
        app = MCPServer("test").streamable_http_app(
            transport_security=cli.transport_security(extra_hosts)
        )
        with TestClient(app) as client:
            local = client.post(
                "/mcp", headers={**headers, "host": "127.0.0.1:8491"}, json=request
            )
            other = client.post(
                "/mcp", headers={**headers, "host": "example.test:8491"}, json=request
            )
            assert local.status_code == 200
            assert other.status_code == (200 if extra_hosts else 421)


def test_client_receives_data_and_expected_errors(monkeypatch, tmp_path):
    fake = FakeClient({"search/activities": []})
    monkeypatch.setattr(garmin_client, "call", lambda op: op(fake))
    monkeypatch.setenv("GARMIN_MCP_DOWNLOAD_DIR", str(tmp_path / "downloads"))

    async def exercise():
        async with Client(server.mcp) as client:
            result = await client.call_tool("garmin_search_activities", {})
            assert not result.is_error
            assert json.loads(result.content[0].text) == {"results": []}

            result = await client.call_tool("garmin_get_hrv", {"date": "2026-01-01"})
            assert not result.is_error
            assert json.loads(result.content[0].text) == server.NO_DATA

            result = await client.call_tool(
                "garmin_download_activity", {"activity_id": 1, "directory": ".."}
            )
            assert result.is_error
            assert "directory must be inside" in result.content[0].text
            assert "GARMIN_MCP_DOWNLOAD_DIR" in result.content[0].text

            result = await client.call_tool("garmin_search_activities", {"north": 1})
            assert result.is_error
            assert "all four" in result.content[0].text

            def rejected_key(op):
                raise garmin_client.ApiKeyError(garmin_client.RECONNECT_HINT)

            monkeypatch.setattr(garmin_client, "call", rejected_key)
            result = await client.call_tool("garmin_get_profile", {})
            assert result.is_error
            assert garmin_client.RECONNECT_HINT in result.content[0].text

            def rate_limited(op):
                raise http_error(429)

            monkeypatch.setattr(garmin_client, "call", rate_limited)
            result = await client.call_tool("garmin_get_hrv", {})
            assert result.is_error
            assert "returned HTTP 429: nope" in result.content[0].text

            def unreachable(op):
                raise ConnectionError("Garmin is unreachable")

            monkeypatch.setattr(garmin_client, "call", unreachable)
            result = await client.call_tool("garmin_get_hrv", {})
            assert result.is_error
            assert "Garmin is unreachable" in result.content[0].text

            def unexpected_error(op):
                raise RuntimeError("private diagnostic")

            monkeypatch.setattr(garmin_client, "call", unexpected_error)
            result = await client.call_tool("garmin_get_profile", {})
            assert result.is_error
            assert "private diagnostic" not in result.content[0].text

    asyncio.run(exercise())
