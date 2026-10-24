import asyncio
import datetime
import json

import pytest
from conftest import FakeClient

from garmin_personal_mcp import activities, garmin_client, server


@pytest.fixture
def client(monkeypatch):
    fake = FakeClient({"search/activities": [], "dailySleep": {"sleepTimeSeconds": 1}})
    monkeypatch.setattr(garmin_client, "call", lambda op: op(fake))
    return fake


def tools():
    return asyncio.run(server.mcp.list_tools())


def test_parse_day_explains_the_expected_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        server.parse_day("10/20/2026")


def test_parse_range_defaults_to_the_week_ending_today():
    first, last = server.parse_range(None, "2026-10-21")
    assert (first, last) == (datetime.date(2026, 10, 15), datetime.date(2026, 10, 21))


def test_parse_range_rejects_an_inverted_range():
    with pytest.raises(ValueError, match="swap"):
        server.parse_range("2026-10-22", "2026-10-21")


def test_every_endpoint_has_a_tool():
    assert len(tools()) == 26


def test_tools_are_read_only_except_the_local_download():
    writers = [tool.name for tool in tools() if not tool.annotations.read_only_hint]
    assert writers == ["garmin_download_activity"]


def test_every_tool_is_described():
    assert all(tool.description and tool.title for tool in tools())


def test_no_data_is_explained(client):
    result = asyncio.run(server.garmin_get_hrv("2026-10-20"))
    assert result == server.NO_DATA


def test_tool_returns_garmin_data(client):
    assert asyncio.run(server.garmin_get_sleep("2026-10-20")) == {"sleepTimeSeconds": 1}


def test_list_results_are_wrapped_so_empty_ones_still_render(client):
    result = asyncio.run(server.mcp.call_tool("garmin_search_activities", {}))
    [content] = result.content
    assert json.loads(content.text) == {"results": []}


def test_search_without_dates_lists_the_most_recent(client):
    asyncio.run(server.garmin_search_activities(limit=5))
    [(path, params)] = client.calls
    assert "startDate" not in params
    assert params["limit"] == 5


def test_search_with_only_an_end_date_uses_the_week_before_it(client):
    asyncio.run(server.garmin_search_activities(end="2026-10-21", favorite=True))
    [(path, params)] = client.calls
    assert params["startDate"] == "2026-10-15"
    assert params["favorite"] == 1


def test_search_rejects_a_partial_bounding_box(client):
    with pytest.raises(activities.ActivitySearchError):
        asyncio.run(server.garmin_search_activities(north=40.0))
    assert client.calls == []


@pytest.fixture
def saved(client, monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_MCP_DOWNLOAD_DIR", str(tmp_path / "fits"))
    saved = {}

    def fake_download(c, activity_id, directory):
        saved["directory"] = directory
        return {}

    monkeypatch.setattr(activities, "download_activity", fake_download)
    return saved


def test_download_defaults_to_the_configured_directory(saved, tmp_path):
    asyncio.run(server.garmin_download_activity(123))
    assert saved["directory"] == tmp_path / "fits"


def test_download_saves_in_a_subfolder_of_the_configured_directory(saved, tmp_path):
    asyncio.run(server.garmin_download_activity(123, directory="races/2026"))
    assert saved["directory"] == (tmp_path / "fits" / "races" / "2026").resolve()


def test_download_accepts_an_absolute_path_inside_the_configured_directory(
    saved, tmp_path
):
    inside = tmp_path / "fits" / "races"
    asyncio.run(server.garmin_download_activity(123, directory=str(inside)))
    assert saved["directory"] == inside.resolve()


@pytest.mark.parametrize("directory", ["..", "races/../../elsewhere", "/"])
def test_download_rejects_a_directory_outside_the_configured_one(saved, directory):
    with pytest.raises(ValueError, match="GARMIN_MCP_DOWNLOAD_DIR"):
        asyncio.run(server.garmin_download_activity(123, directory=directory))
    assert saved == {}


def test_download_rejects_an_absolute_path_outside_the_configured_one(saved, tmp_path):
    with pytest.raises(ValueError, match="must be inside"):
        asyncio.run(
            server.garmin_download_activity(123, directory=str(tmp_path / "other"))
        )
    assert saved == {}


def test_download_rejects_a_symlink_that_leads_outside(saved, tmp_path):
    (tmp_path / "fits").mkdir()
    (tmp_path / "outside").mkdir()
    (tmp_path / "fits" / "escape").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="must be inside"):
        asyncio.run(server.garmin_download_activity(123, directory="escape"))
    assert saved == {}
