import datetime

import pytest
from conftest import FakeClient, http_error
from garmin_personal_api import HttpError

from garmin_personal_mcp import day

DAY = datetime.date(2026, 10, 20)


def test_day_loads_every_section(client):
    record = day.get_day(client, DAY)
    assert set(record) == {"date", *day.day_sections(DAY)}
    assert record["date"] == "2026-10-20"
    assert len(client.calls) == len(day.day_sections(DAY))


def test_missing_section_does_not_sink_the_rest():
    client = FakeClient(
        {"hrv-service": http_error(404), "usersummary/daily": {"totalSteps": 9120}}
    )
    record = day.get_day(client, DAY)
    assert "404" in record["hrv"]["error"]
    assert record["summary"] == {"totalSteps": 9120}


def test_expired_token_propagates_so_the_call_can_retry():
    client = FakeClient({"sleep-service": http_error(401)})
    with pytest.raises(HttpError):
        day.get_day(client, DAY)
