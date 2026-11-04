import asyncio
import json
import sys

import requests
from conftest import FakeClient
from garmin_personal_api import HttpError
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

            def unexpected_error(op):
                raise RuntimeError("private diagnostic")

            monkeypatch.setattr(garmin_client, "call", unexpected_error)
            result = await client.call_tool("garmin_get_profile", {})
            assert result.is_error
            assert "private diagnostic" not in result.content[0].text

    asyncio.run(exercise())


def test_client_sees_why_garmin_requests_failed(monkeypatch):
    def failing_with(exc):
        def call(op):
            raise exc

        return call

    def http_error(status, text):
        return HttpError(
            status_code=status,
            method="GET",
            url="https://apis.garmin.com/wellness-api/rest/hrv",
            response_text=text,
        )

    cases = [
        (http_error(429, "rate limited"), ["returned HTTP 429: rate limited", "wait"]),
        (http_error(503, ""), ["returned HTTP 503", "try again later"]),
        (http_error(404, "not found"), ["returned HTTP 404: not found"]),
        (
            requests.ConnectionError("connection refused"),
            ["Couldn't reach Garmin (ConnectionError)", "internet connection"],
        ),
        (
            PermissionError(13, "Permission denied", "/downloads/activity-1.zip"),
            ["Couldn't save /downloads/activity-1.zip: Permission denied"],
        ),
    ]

    async def exercise():
        async with Client(server.mcp) as client:
            for exc, expected in cases:
                monkeypatch.setattr(garmin_client, "call", failing_with(exc))
                result = await client.call_tool("garmin_get_hrv", {})
                assert result.is_error
                text = result.content[0].text
                for fragment in expected:
                    assert fragment in text
                assert "Personal API key" not in text

    asyncio.run(exercise())


def test_download_that_is_not_a_zip_tells_the_client_why(monkeypatch, tmp_path):
    fake = FakeClient()
    fake.downloads[123] = b"<html>maintenance</html>"
    monkeypatch.setattr(garmin_client, "call", lambda op: op(fake))
    monkeypatch.setenv("GARMIN_MCP_DOWNLOAD_DIR", str(tmp_path))

    async def exercise():
        async with Client(server.mcp) as client:
            return await client.call_tool(
                "garmin_download_activity", {"activity_id": 123}
            )

    result = asyncio.run(exercise())
    assert result.is_error
    assert "wasn't a ZIP file (24 bytes), so nothing was saved" in (
        result.content[0].text
    )
    assert not (tmp_path / "activity-123.zip").exists()
