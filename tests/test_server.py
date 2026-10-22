import asyncio
import datetime

import pytest
from garmin_personal_api import HttpError

from garmin_personal_mcp import cli, garmin, server


class RecordingClient:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "get_daily_hrv":
                raise HttpError(
                    status_code=404, method="GET", url="/hrv", response_text=""
                )
            return {"endpoint": name}

        return record


@pytest.fixture
def client(monkeypatch):
    fake = RecordingClient()
    monkeypatch.setattr(garmin, "call", lambda op: op(fake))
    return fake


def test_parse_range_defaults_to_last_seven_days():
    first, last = server.parse_range(None, "2026-10-21")
    assert (first, last) == (datetime.date(2026, 10, 15), datetime.date(2026, 10, 21))


def test_parse_range_rejects_inverted_range():
    with pytest.raises(ValueError):
        server.parse_range("2026-10-22", "2026-10-21")


def test_get_day_collects_every_section(client):
    record = asyncio.run(server.garmin_get_day("2026-10-21"))
    assert record["date"] == "2026-10-21"
    assert record["summary"] == {"endpoint": "get_daily_summaries"}
    assert "404" in record["hrv"]["error"]
    assert set(record) == {"date", *server.day_sections(datetime.date.today())}


def test_activities_without_dates_lists_most_recent(client):
    asyncio.run(server.garmin_activities(limit=5, offset=10))
    assert client.calls == [
        (
            "search_activities",
            (),
            {
                "start": 10,
                "limit": 5,
                "start_date": None,
                "end_date": None,
                "activity_type": None,
            },
        )
    ]


def test_range_tool_passes_parsed_dates(client):
    asyncio.run(server.garmin_hrv("2026-10-01", "2026-10-21"))
    assert client.calls == [
        (
            "get_daily_hrv_summaries",
            (datetime.date(2026, 10, 1), datetime.date(2026, 10, 21)),
            {},
        )
    ]


def test_raw_get_requires_absolute_path(client):
    with pytest.raises(ValueError):
        asyncio.run(server.garmin_get("@evil.example/steal"))
    assert client.calls == []


def test_raw_get_forwards_path_and_params(client):
    asyncio.run(server.garmin_get("/hrv-service/hrv/2026-10-21", {"a": "b"}))
    assert client.calls == [
        ("get", ("/hrv-service/hrv/2026-10-21",), {"params": {"a": "b"}})
    ]


def test_every_tool_is_read_only():
    tools = asyncio.run(server.mcp.list_tools())
    assert len(tools) == 14
    assert all(tool.annotations.readOnlyHint for tool in tools)


def test_transport_security_accepts_extra_host_with_any_port():
    settings = cli.transport_security(["familiar-v1.example.ts.net"])
    assert "familiar-v1.example.ts.net:*" in settings.allowed_hosts
    assert "127.0.0.1:*" in settings.allowed_hosts
    assert "https://familiar-v1.example.ts.net:*" in settings.allowed_origins
