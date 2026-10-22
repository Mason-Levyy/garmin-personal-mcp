import datetime
import io
import zipfile

import pytest

from garmin_personal_mcp import activities


def test_default_search_sends_only_paging_and_children_flag(client):
    activities.search_activities(
        client, activities.ActivitySearch(), limit=20, offset=40
    )
    assert client.calls == [
        (
            "/activitylist-service/activities/search/activities",
            {"start": 40, "limit": 20, "excludeChildren": "true"},
        )
    ]


def test_search_maps_every_filter_to_garmin_names():
    search = activities.ActivitySearch(
        start=datetime.date(2026, 9, 1),
        end=datetime.date(2026, 9, 30),
        search="tempo",
        activity_type="running",
        activity_subtype="trail_running",
        excluded_activity_subtypes=("treadmill_running", "track_running"),
        event_type="race",
        favorite=False,
        exclude_children=False,
        sort_by="distance",
        sort_order="asc",
        min_distance=5000,
        max_distance=42195,
        min_duration=1200,
        max_duration=14400,
        min_elapsed_duration=1300,
        max_elapsed_duration=15000,
        min_elevation=10,
        max_elevation=2000,
        min_avg_power=200,
        start_area=activities.BoundingBox(
            north=40.1, south=39.9, east=-104.8, west=-105.1
        ),
        min_max_depth=500,
        max_max_depth=3000,
        deco_dive=True,
        min_bottom_time=600,
        max_bottom_time=3600,
        required_fields=("avgPower",),
    )
    assert search.params() == {
        "startDate": "2026-09-01",
        "endDate": "2026-09-30",
        "search": "tempo",
        "activityType": "running",
        "activitySubType": "trail_running",
        "excludedActivitySubType": ["treadmill_running", "track_running"],
        "eventType": "race",
        "favorite": 0,
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


def test_favorites_only_sends_one():
    assert activities.ActivitySearch(favorite=True).params()["favorite"] == 1


def test_bounding_box_is_all_or_nothing():
    assert activities.bounding_box(None, None, None, None) is None
    assert activities.bounding_box(1, 0, 1, 0) == activities.BoundingBox(1, 0, 1, 0)
    with pytest.raises(activities.ActivitySearchError, match="all four"):
        activities.bounding_box(1, None, 1, 0)


def test_activity_detail_and_workout_paths(client):
    activities.get_activity(client, 123)
    activities.get_activity_workouts(client, 123)
    assert [path for path, _ in client.calls] == [
        "/activity-service/activity/123",
        "/activity-service/activity/123/workouts",
    ]


def test_download_saves_zip_and_lists_contents(client, tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("123_ACTIVITY.fit", b"fit-bytes")
    client.downloads[123] = buffer.getvalue()

    result = activities.download_activity(client, 123, tmp_path / "garmin")

    saved = tmp_path / "garmin" / "activity-123.zip"
    assert saved.read_bytes() == buffer.getvalue()
    assert result == {
        "path": str(saved),
        "bytes": len(buffer.getvalue()),
        "files": ["123_ACTIVITY.fit"],
    }
