import datetime

import pytest
from conftest import FakeClient, load_fixture

from garmin_personal_mcp import (
    daily_summary,
    hrv,
    nutrition,
    profile,
    sleep,
    weight,
    wellness,
    womens_health,
)

D = datetime.date
DAY = D(2026, 10, 20)
WEEK = (D(2026, 10, 14), D(2026, 10, 20))

SINGLE_REQUEST_CASES = [
    (
        lambda c: daily_summary.get_daily_summary(c, DAY),
        "/usersummary-service/usersummary/daily",
        {"calendarDate": "2026-10-20"},
    ),
    (
        lambda c: wellness.get_wellness_activities(c, *WEEK),
        "/wellnessactivity-service/activity/summary/range/2026-10-14/2026-10-20",
        None,
    ),
    (
        lambda c: sleep.get_sleep(c, DAY),
        "/sleep-service/sleep/dailySleep",
        {"date": "2026-10-20"},
    ),
    (lambda c: hrv.get_hrv(c, DAY), "/hrv-service/hrv/2026-10-20", None),
    (
        lambda c: hrv.get_hrv_summaries(c, *WEEK),
        "/hrv-service/hrv/daily/2026-10-14/2026-10-20",
        None,
    ),
    (
        lambda c: weight.get_weight(c, *WEEK),
        "/weight-service/weight/range/2026-10-14/2026-10-20",
        {"includeAll": "false"},
    ),
    (
        lambda c: weight.get_weigh_ins(c, *WEEK),
        "/weight-service/weight/all/2026-10-14/2026-10-20",
        None,
    ),
    (
        lambda c: weight.get_weight_goals(c, *WEEK),
        "/goal-service/goal/user/effective/weightgoal/2026-10-14/2026-10-20",
        None,
    ),
    (
        lambda c: nutrition.get_food_log(c, DAY, meal_id=3),
        "/nutrition-service/food/logs/2026-10-20",
        {
            "mealId": 3,
            "includeGoals": "true",
            "includeNutrition": "true",
            "includeMedia": "false",
        },
    ),
    (
        lambda c: profile.get_settings(c),
        "/userprofile-service/userprofile/settings",
        None,
    ),
    (
        lambda c: profile.get_heart_rate_zones(c, generate_defaults=False),
        "/biometric-service/heartRateZones/v2",
        {"generateDefaults": "false"},
    ),
    (
        lambda c: profile.get_fitness_age(c, DAY),
        "/fitnessage-service/fitnessage/v2/2026-10-20",
        {"fullHistoryScan": "true"},
    ),
    (
        lambda c: womens_health.get_cycle_summary(c, DAY),
        "/periodichealth-service/menstrualcycle/summary/2026-10-20",
        None,
    ),
    (
        lambda c: womens_health.get_cycle_day(
            c, DAY, today=D(2026, 10, 22), skip_baby_movement=True
        ),
        "/periodichealth-service/menstrualcycle/dayview/2026-10-20",
        {
            "todayDate": "2026-10-22",
            "reducedResponse": "false",
            "skipbm": "true",
            "includeAnalysis": "false",
        },
    ),
]


@pytest.mark.parametrize(("read", "path", "params"), SINGLE_REQUEST_CASES)
def test_endpoint_request_shape(client, read, path, params):
    read(client)
    assert client.calls == [(path, params)]


@pytest.mark.parametrize(
    ("metric", "windows", "first_window_end"),
    [
        ("steps", 3, "2026-01-28"),
        ("stress", 3, "2026-01-28"),
        ("hydration", 2, "2026-01-31"),
    ],
)
def test_stats_split_long_ranges_at_the_documented_limit(
    metric, windows, first_window_end
):
    client = FakeClient({metric: lambda path, params: [path]})
    rows = daily_summary.get_stats(client, metric, D(2026, 1, 1), D(2026, 3, 1))
    assert len(rows) == windows
    assert rows[0] == (
        f"/usersummary-service/stats/{metric}/daily/2026-01-01/{first_window_end}"
    )


def test_daily_summaries_merge_windowed_pages():
    client = FakeClient({"dailysummaries": load_fixture("daily_summaries.json")})
    result = daily_summary.get_daily_summaries(client, D(2025, 1, 1), D(2026, 6, 1))
    assert len(client.calls) == 2
    assert client.calls[0][1] == {"startDate": "2025-01-01", "endDate": "2025-12-31"}
    assert [row["calendarDate"] for row in result["data"]] == ["2026-10-20"] * 2


def test_daily_summaries_tolerate_empty_pages(client):
    assert daily_summary.get_daily_summaries(client, *WEEK) == {"data": []}


def test_sleep_summaries_split_at_31_days():
    client = FakeClient({"dailySleepSummaries": []})
    sleep.get_sleep_summaries(client, D(2026, 1, 1), D(2026, 2, 1))
    assert [params for _, params in client.calls] == [
        {"startDate": "2026-01-01", "endDate": "2026-01-31"},
        {"startDate": "2026-02-01", "endDate": "2026-02-01"},
    ]


def test_heart_rate_leaves_out_samples_by_default():
    client = FakeClient({"dailyHeartRate": load_fixture("heart_rate.json")})
    record = wellness.get_heart_rate(client, DAY)
    assert record["restingHeartRate"] == 52
    assert "heartRateValues" not in record
    assert "heartRateValueDescriptors" not in record
    assert "abnormalHRValuesArray" in record


def test_heart_rate_samples_on_request():
    client = FakeClient({"dailyHeartRate": load_fixture("heart_rate.json")})
    record = wellness.get_heart_rate(client, DAY, include_samples=True)
    assert len(record["heartRateValues"]) == 3


def test_spo2_keeps_hourly_averages_but_drops_single_readings():
    client = FakeClient({"spo2acclimation": load_fixture("spo2.json")})
    record = wellness.get_spo2(client, DAY)
    assert "spO2SingleValues" not in record
    assert record["spO2HourlyAverages"] == [[1792483200000, 96]]


def test_body_battery_drops_full_resolution_readings():
    client = FakeClient({"bodyBattery": load_fixture("body_battery.json")})
    [report] = wellness.get_body_battery(client, DAY, DAY)
    assert "bodyBatteryValuesArray" not in report
    assert report["bodyBatteryActivityEvent"][0]["eventType"] == "SLEEP"
    assert client.calls[0][1] == {"startDate": "2026-10-20", "endDate": "2026-10-20"}


def test_body_battery_keeps_chunked_readings():
    client = FakeClient({"bodyBattery": load_fixture("body_battery.json")})
    [report] = wellness.get_body_battery(client, DAY, DAY, chunks=24)
    assert "bodyBatteryValuesArray" in report
    assert client.calls[0][1]["chunks"] == 24
