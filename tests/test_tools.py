import asyncio
import io
import json
import zipfile

import pytest
from conftest import FakeClient, load_fixture
from mcp import Client

from garmin_personal_mcp import garmin_client, server

DAY = "2026-10-20"
START, END = "2026-10-14", "2026-10-20"
RANGE = {"start": START, "end": END}
RANGE_PARAMS = {"startDate": START, "endDate": END}

SEARCH_ARGUMENTS = {
    **RANGE,
    "search": "tempo",
    "activity_type": "running",
    "activity_subtype": "trail_running",
    "excluded_activity_subtypes": ["treadmill_running"],
    "event_type": "race",
    "favorite": True,
    "exclude_children": False,
    "sort_by": "distance",
    "sort_order": "asc",
    "min_distance": 5000,
    "max_distance": 42195,
    "min_duration": 1200,
    "max_duration": 14400,
    "min_elapsed_duration": 1300,
    "max_elapsed_duration": 15000,
    "min_elevation": 10,
    "max_elevation": 2000,
    "min_avg_power": 200,
    "north": 40.1,
    "south": 39.9,
    "east": -104.8,
    "west": -105.1,
    "min_max_depth": 500,
    "max_max_depth": 3000,
    "deco_dive": True,
    "min_bottom_time": 600,
    "max_bottom_time": 3600,
    "required_fields": ["avgPower"],
    "limit": 5,
    "offset": 10,
}
SEARCH_PARAMS = {
    "start": 10,
    "limit": 5,
    **RANGE_PARAMS,
    "search": "tempo",
    "activityType": "running",
    "activitySubType": "trail_running",
    "excludedActivitySubType": ["treadmill_running"],
    "eventType": "race",
    "favorite": 1,
    "excludeChildren": "false",
    "sortBy": "distance",
    "sortOrder": "asc",
    "minDistance": 5000,
    "maxDistance": 42195,
    "minDuration": 1200,
    "maxDuration": 14400,
    "minElapsedDuration": 1300,
    "maxElapsedDuration": 15000,
    "minElevation": 10,
    "maxElevation": 2000,
    "minAvgPower": 200,
    "upperLatitude": 40.1,
    "lowerLatitude": 39.9,
    "rightLongitude": -104.8,
    "leftLongitude": -105.1,
    "lowerMaxDepth": 500,
    "upperMaxDepth": 3000,
    "decoDive": "true",
    "minBottomTime": 600,
    "maxBottomTime": 3600,
    "requiredField": ["avgPower"],
}

TOOL_REQUESTS = {
    "garmin_get_day": (
        {"date": DAY},
        [
            ("/usersummary-service/usersummary/daily", {"calendarDate": DAY}),
            ("/sleep-service/sleep/dailySleep", {"date": DAY}),
            (f"/hrv-service/hrv/daily/{DAY}/{DAY}", None),
            (
                "/wellness-service/wellness/bodyBattery/reports/daily",
                {"startDate": DAY, "endDate": DAY},
            ),
            (f"/usersummary-service/stats/stress/daily/{DAY}/{DAY}", None),
            (
                "/activitylist-service/activities/search/activities",
                {
                    "start": 0,
                    "limit": 20,
                    "startDate": DAY,
                    "endDate": DAY,
                    "excludeChildren": "true",
                },
            ),
        ],
    ),
    "garmin_get_daily_summary": (
        {"date": DAY},
        [("/usersummary-service/usersummary/daily", {"calendarDate": DAY})],
    ),
    "garmin_get_daily_summaries": (
        RANGE,
        [("/usersummary-service/v2/dailysummaries", RANGE_PARAMS)],
    ),
    "garmin_get_steps": (
        RANGE,
        [(f"/usersummary-service/stats/steps/daily/{START}/{END}", None)],
    ),
    "garmin_get_stress": (
        RANGE,
        [(f"/usersummary-service/stats/stress/daily/{START}/{END}", None)],
    ),
    "garmin_get_hydration": (
        RANGE,
        [(f"/usersummary-service/stats/hydration/daily/{START}/{END}", None)],
    ),
    "garmin_get_body_battery": (
        {**RANGE, "chunks": 24},
        [
            (
                "/wellness-service/wellness/bodyBattery/reports/daily",
                {**RANGE_PARAMS, "chunks": 24},
            )
        ],
    ),
    "garmin_get_heart_rate": (
        {"date": DAY},
        [("/wellness-service/wellness/dailyHeartRate", {"date": DAY})],
    ),
    "garmin_get_spo2": (
        {"date": DAY},
        [(f"/wellness-service/wellness/daily/spo2acclimation/{DAY}", None)],
    ),
    "garmin_get_wellness_activities": (
        RANGE,
        [(f"/wellnessactivity-service/activity/summary/range/{START}/{END}", None)],
    ),
    "garmin_get_sleep": (
        {"date": DAY},
        [("/sleep-service/sleep/dailySleep", {"date": DAY})],
    ),
    "garmin_get_sleep_summaries": (
        RANGE,
        [("/sleep-service/sleep/dailySleepSummariesByDate", RANGE_PARAMS)],
    ),
    "garmin_get_hrv": ({"date": DAY}, [(f"/hrv-service/hrv/{DAY}", None)]),
    "garmin_get_hrv_summaries": (
        RANGE,
        [(f"/hrv-service/hrv/daily/{START}/{END}", None)],
    ),
    "garmin_get_weight": (
        {**RANGE, "include_all": True},
        [(f"/weight-service/weight/range/{START}/{END}", {"includeAll": "true"})],
    ),
    "garmin_get_weight_goals": (
        RANGE,
        [(f"/goal-service/goal/user/effective/weightgoal/{START}/{END}", None)],
    ),
    "garmin_get_food_log": (
        {
            "date": DAY,
            "meal_id": 3,
            "include_goals": False,
            "include_nutrition": False,
            "include_media": True,
        },
        [
            (
                f"/nutrition-service/food/logs/{DAY}",
                {
                    "mealId": 3,
                    "includeGoals": "false",
                    "includeNutrition": "false",
                    "includeMedia": "true",
                },
            )
        ],
    ),
    "garmin_search_activities": (
        SEARCH_ARGUMENTS,
        [("/activitylist-service/activities/search/activities", SEARCH_PARAMS)],
    ),
    "garmin_get_activity": (
        {"activity_id": 123},
        [("/activity-service/activity/123", None)],
    ),
    "garmin_get_activity_workouts": (
        {"activity_id": 123},
        [("/activity-service/activity/123/workouts", None)],
    ),
    "garmin_get_profile": ({}, [("/userprofile-service/userprofile/settings", None)]),
    "garmin_get_heart_rate_zones": (
        {"generate_defaults": False},
        [("/biometric-service/heartRateZones/v2", {"generateDefaults": "false"})],
    ),
    "garmin_get_fitness_age": (
        {"date": DAY, "full_history_scan": False},
        [(f"/fitnessage-service/fitnessage/v2/{DAY}", {"fullHistoryScan": "false"})],
    ),
    "garmin_get_menstrual_cycle": (
        {"date": DAY},
        [(f"/periodichealth-service/menstrualcycle/summary/{DAY}", None)],
    ),
    "garmin_get_menstrual_day": (
        {
            "date": DAY,
            "today": "2026-10-22",
            "reduced": True,
            "skip_baby_movement": True,
            "include_analysis": True,
        },
        [
            (
                f"/periodichealth-service/menstrualcycle/dayview/{DAY}",
                {
                    "todayDate": "2026-10-22",
                    "reducedResponse": "true",
                    "skipbm": "true",
                    "includeAnalysis": "true",
                },
            )
        ],
    ),
}
DOWNLOAD_TOOL = "garmin_download_activity"


def call_tool(name, arguments):
    result = asyncio.run(server.mcp.call_tool(name, arguments))
    assert not result.is_error, result.content
    return json.loads(result.content[0].text)


@pytest.fixture
def garmin(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(garmin_client, "call", lambda op: op(fake))
    return fake


def test_every_tool_has_a_request_case():
    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    assert names == {*TOOL_REQUESTS, DOWNLOAD_TOOL}


@pytest.mark.parametrize(("name", "case"), TOOL_REQUESTS.items())
def test_tool_sends_its_arguments_to_garmin(garmin, name, case):
    arguments, requests = case
    call_tool(name, arguments)
    assert garmin.calls == requests


@pytest.mark.parametrize(
    ("name", "route", "fixture", "sample_field"),
    [
        (
            "garmin_get_heart_rate",
            "dailyHeartRate",
            "heart_rate.json",
            "heartRateValues",
        ),
        ("garmin_get_spo2", "spo2acclimation", "spo2.json", "spO2SingleValues"),
    ],
)
def test_include_samples_reaches_the_response(
    garmin, name, route, fixture, sample_field
):
    garmin.routes[route] = load_fixture(fixture)
    assert sample_field not in call_tool(name, {"date": DAY})
    assert sample_field in call_tool(name, {"date": DAY, "include_samples": True})


def test_download_saves_the_requested_activity_in_the_requested_folder(
    garmin, monkeypatch, tmp_path
):
    monkeypatch.setenv("GARMIN_MCP_DOWNLOAD_DIR", str(tmp_path))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("123_ACTIVITY.fit", b"fit-bytes")
    garmin.downloads[123] = buffer.getvalue()

    result = call_tool(DOWNLOAD_TOOL, {"activity_id": 123, "directory": "races"})

    saved = (tmp_path / "races" / "activity-123.zip").resolve()
    assert saved.read_bytes() == buffer.getvalue()
    assert result["path"] == str(saved)


def test_download_that_is_not_a_zip_tells_the_model_why(garmin, monkeypatch, tmp_path):
    monkeypatch.setenv("GARMIN_MCP_DOWNLOAD_DIR", str(tmp_path))
    garmin.downloads[123] = b"<html>maintenance</html>"

    async def download():
        async with Client(server.mcp) as client:
            return await client.call_tool(DOWNLOAD_TOOL, {"activity_id": 123})

    result = asyncio.run(download())

    assert result.is_error
    assert "wasn't a ZIP file (24 bytes), so nothing was saved" in (
        result.content[0].text
    )
    assert not (tmp_path / "activity-123.zip").exists()
