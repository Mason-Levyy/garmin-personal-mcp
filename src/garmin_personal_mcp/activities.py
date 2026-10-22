import datetime
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .garmin_api import query


class ActivitySearchError(ValueError):
    pass


@dataclass(frozen=True)
class BoundingBox:
    north: float
    south: float
    east: float
    west: float


@dataclass(frozen=True)
class ActivitySearch:
    start: datetime.date | None = None
    end: datetime.date | None = None
    search: str | None = None
    activity_type: str | None = None
    activity_subtype: str | None = None
    excluded_activity_subtypes: tuple[str, ...] = ()
    event_type: str | None = None
    favorite: bool | None = None
    exclude_children: bool = True
    sort_by: str | None = None
    sort_order: str | None = None
    min_distance: int | None = None
    max_distance: int | None = None
    min_duration: int | None = None
    max_duration: int | None = None
    min_elapsed_duration: int | None = None
    max_elapsed_duration: int | None = None
    min_elevation: int | None = None
    max_elevation: int | None = None
    min_avg_power: int | None = None
    start_area: BoundingBox | None = None
    min_max_depth: int | None = None
    max_max_depth: int | None = None
    deco_dive: bool | None = None
    min_bottom_time: int | None = None
    max_bottom_time: int | None = None
    required_fields: tuple[str, ...] = ()

    def params(self) -> dict:
        area = {}
        if self.start_area is not None:
            area = {
                "upperLatitude": self.start_area.north,
                "lowerLatitude": self.start_area.south,
                "rightLongitude": self.start_area.east,
                "leftLongitude": self.start_area.west,
            }
        favorite = None
        if self.favorite is not None:
            favorite = int(self.favorite)
        return query(
            startDate=self.start,
            endDate=self.end,
            search=self.search,
            activityType=self.activity_type,
            activitySubType=self.activity_subtype,
            excludedActivitySubType=list(self.excluded_activity_subtypes),
            eventType=self.event_type,
            favorite=favorite,
            excludeChildren=self.exclude_children,
            sortBy=self.sort_by,
            sortOrder=self.sort_order,
            minDistance=self.min_distance,
            maxDistance=self.max_distance,
            minDuration=self.min_duration,
            maxDuration=self.max_duration,
            minElapsedDuration=self.min_elapsed_duration,
            maxElapsedDuration=self.max_elapsed_duration,
            minElevation=self.min_elevation,
            maxElevation=self.max_elevation,
            minAvgPower=self.min_avg_power,
            **area,
            lowerMaxDepth=self.min_max_depth,
            upperMaxDepth=self.max_max_depth,
            decoDive=self.deco_dive,
            minBottomTime=self.min_bottom_time,
            maxBottomTime=self.max_bottom_time,
            requiredField=list(self.required_fields),
        )


def bounding_box(
    north: float | None, south: float | None, east: float | None, west: float | None
) -> BoundingBox | None:
    edges = (north, south, east, west)
    if all(edge is None for edge in edges):
        return None
    if any(edge is None for edge in edges):
        raise ActivitySearchError(
            "Garmin filters by start location only with all four edges: pass "
            "north, south, east, and west latitudes/longitudes, or none of them."
        )
    return BoundingBox(*edges)


def search_activities(
    client, filters: ActivitySearch, *, limit: int, offset: int
) -> list | None:
    return client.get(
        "/activitylist-service/activities/search/activities",
        params={**query(start=offset, limit=limit), **filters.params()},
    )


def get_activity(client, activity_id: int) -> dict | None:
    return client.get(f"/activity-service/activity/{activity_id}")


def get_activity_workouts(client, activity_id: int) -> list | None:
    return client.get(f"/activity-service/activity/{activity_id}/workouts")


def download_activity(client, activity_id: int, directory: Path) -> dict:
    content = client.download_activity(activity_id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"activity-{activity_id}.zip"
    path.write_bytes(content)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        files = archive.namelist()
    return {"path": str(path), "bytes": len(content), "files": files}
