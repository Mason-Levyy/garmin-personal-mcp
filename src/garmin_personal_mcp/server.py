import asyncio
import datetime
from collections.abc import Callable

from garmin_personal_api import GarminPersonalApiClient
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import garmin

mcp = FastMCP("garmin")

READS_GARMIN = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
DEFAULT_SPAN_DAYS = 7


def parse_day(value: str | None) -> datetime.date:
    if value is None:
        return datetime.date.today()
    return datetime.date.fromisoformat(value)


def parse_range(
    start: str | None, end: str | None
) -> tuple[datetime.date, datetime.date]:
    end_day = parse_day(end)
    if start is None:
        return end_day - datetime.timedelta(days=DEFAULT_SPAN_DAYS - 1), end_day
    start_day = parse_day(start)
    if start_day > end_day:
        raise ValueError("start must be on or before end")
    return start_day, end_day


async def fetch[T](op: Callable[[GarminPersonalApiClient], T]) -> T:
    return await asyncio.to_thread(garmin.call, op)


def day_sections(day: datetime.date) -> dict:
    return {
        "summary": lambda c: c.get_daily_summaries(day, day),
        "sleep": lambda c: c.get_daily_sleep_summaries(day, day),
        "hrv": lambda c: c.get_daily_hrv(day),
        "body_battery": lambda c: c.get_daily_body_battery(day, day),
        "stress": lambda c: c.get_daily_stress(day, day),
        "activities": lambda c: c.search_activities(start_date=day, end_date=day),
    }


@mcp.tool(title="Get day overview", annotations=READS_GARMIN)
async def garmin_get_day(date: str | None = None) -> dict:
    """One day at a glance: daily summary (steps, calories, resting HR, intensity
    minutes), sleep, HRV, body battery, stress, and activities. A section that
    Garmin has no data for yet comes back as {"error": ...}.

    date: YYYY-MM-DD (default: today).
    """
    day = parse_day(date)
    record = await fetch(lambda c: garmin.read_sections(c, day_sections(day)))
    return {"date": day.isoformat(), **record}


@mcp.tool(title="Daily summaries", annotations=READS_GARMIN)
async def garmin_daily_summaries(start: str | None = None, end: str | None = None):
    """Per-day totals: steps, distance, calories, floors, intensity minutes,
    resting/min/max heart rate, stress and body battery highlights.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_summaries(first, last))


@mcp.tool(title="Sleep detail", annotations=READS_GARMIN)
async def garmin_sleep(date: str | None = None):
    """Full sleep record for the night ending on date: stages, score, timings,
    and overnight HR/SpO2/respiration where the device records them.

    date: YYYY-MM-DD (default: today, i.e. last night).
    """
    day = parse_day(date)
    return await fetch(lambda c: c.get_daily_sleep(day))


@mcp.tool(title="Sleep summaries", annotations=READS_GARMIN)
async def garmin_sleep_summaries(start: str | None = None, end: str | None = None):
    """Nightly sleep summaries (duration, stages, score) across a date range.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_sleep_summaries(first, last))


@mcp.tool(title="HRV", annotations=READS_GARMIN)
async def garmin_hrv(start: str | None = None, end: str | None = None):
    """Overnight heart-rate variability per night, with weekly average,
    baseline band, and status.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_hrv_summaries(first, last))


@mcp.tool(title="Body battery", annotations=READS_GARMIN)
async def garmin_body_battery(start: str | None = None, end: str | None = None):
    """Daily body battery charged/drained and levels.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_body_battery(first, last))


@mcp.tool(title="Stress", annotations=READS_GARMIN)
async def garmin_stress(start: str | None = None, end: str | None = None):
    """Daily average and max stress levels.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_stress(first, last))


@mcp.tool(title="Steps", annotations=READS_GARMIN)
async def garmin_steps(start: str | None = None, end: str | None = None):
    """Daily step totals, distance, and step goal.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_daily_steps(first, last))


@mcp.tool(title="Heart rate", annotations=READS_GARMIN)
async def garmin_heart_rate(date: str | None = None):
    """Resting, min, and max heart rate for a day plus the all-day HR samples.

    date: YYYY-MM-DD (default: today).
    """
    day = parse_day(date)
    return await fetch(lambda c: c.get_daily_heart_rate(day))


@mcp.tool(title="Weight", annotations=READS_GARMIN)
async def garmin_weight(start: str | None = None, end: str | None = None):
    """Weigh-ins and body composition recorded in Garmin Connect (weights in grams).

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: c.get_weight_measurements(first, last))


@mcp.tool(title="List activities", annotations=READS_GARMIN)
async def garmin_activities(
    start: str | None = None,
    end: str | None = None,
    activity_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """Recorded activities, newest first: name, type, start time, duration,
    distance, HR, calories, training effect. Pass an activity_id to
    garmin_activity for the full record.

    start, end: YYYY-MM-DD inclusive; omit both for the most recent activities.
    activity_type: Garmin type key such as running, cycling, strength_training.
    """
    first, last = None, None
    if start is not None or end is not None:
        first, last = parse_range(start, end)
    return await fetch(
        lambda c: c.search_activities(
            start=offset,
            limit=limit,
            start_date=first,
            end_date=last,
            activity_type=activity_type,
        )
    )


@mcp.tool(title="Activity detail", annotations=READS_GARMIN)
async def garmin_activity(activity_id: int) -> dict:
    """Full record of one activity (summary metrics, laps/splits) plus any
    structured workout it followed."""
    sections = {
        "activity": lambda c: c.get_activity(activity_id),
        "workouts": lambda c: c.get_activity_workouts(activity_id),
    }
    return await fetch(lambda c: garmin.read_sections(c, sections))


@mcp.tool(title="Profile and HR zones", annotations=READS_GARMIN)
async def garmin_profile() -> dict:
    """Profile settings (units, birth date, height, weight, VO2 max, lactate
    threshold) and heart-rate zones."""
    sections = {
        "settings": lambda c: c.get_user_profile_settings(),
        "heart_rate_zones": lambda c: c.get_heart_rate_zones(),
    }
    return await fetch(lambda c: garmin.read_sections(c, sections))


@mcp.tool(title="Raw Personal API GET", annotations=READS_GARMIN)
async def garmin_get(path: str, params: dict[str, str] | None = None):
    """GET any Personal API endpoint not covered above, e.g.
    /fitnessage-service/fitnessage/v2/2026-10-21,
    /wellness-service/wellness/daily/spo2acclimation/2026-10-21,
    /usersummary-service/stats/hydration/daily/2026-10-01/2026-10-21,
    /nutrition-service/food/logs/2026-10-21. Reference:
    https://developer.garmin.com/gc-developer-program/personal/swagger-docs/

    path: must start with "/".
    """
    if not path.startswith("/"):
        raise ValueError('path must start with "/"')
    return await fetch(lambda c: c.get(path, params=params))
