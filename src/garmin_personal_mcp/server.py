import asyncio
import datetime
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import (
    activities,
    config,
    daily_summary,
    day,
    garmin_client,
    hrv,
    nutrition,
    profile,
    sleep,
    weight,
    wellness,
    womens_health,
)

mcp = FastMCP("garmin")

READS_GARMIN = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
SAVES_LOCAL_FILE = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True
)

DEFAULT_SPAN_DAYS = 7
NO_DATA = {
    "no_data": "Garmin returned nothing for this request: nothing was recorded "
    "for that date yet, or your device doesn't measure it."
}


def parse_day(value: str | None) -> datetime.date:
    if value is None:
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"dates must be YYYY-MM-DD, got {value!r}") from None


def parse_range(
    start: str | None, end: str | None
) -> tuple[datetime.date, datetime.date]:
    end_day = parse_day(end)
    if start is None:
        return end_day - datetime.timedelta(days=DEFAULT_SPAN_DAYS - 1), end_day
    start_day = parse_day(start)
    if start_day > end_day:
        raise ValueError(
            f"start ({start_day}) must be on or before end ({end_day}); swap them"
        )
    return start_day, end_day


async def fetch(op: Callable[[Any], Any]) -> dict:
    """MCP clients render a bare list as one content block per item, so an
    empty list would reach the model as nothing at all."""
    result = await asyncio.to_thread(garmin_client.call, op)
    if result is None:
        return NO_DATA
    if isinstance(result, list):
        return {"results": result}
    return result


@mcp.tool(title="Get day overview", annotations=READS_GARMIN)
async def garmin_get_day(date: str | None = None) -> dict:
    """One day at a glance: daily summary (steps, calories, intensity minutes,
    resting HR, stress, body battery), last night's sleep, HRV, body battery,
    stress, and the day's activities. A section Garmin has no data for yet
    comes back as {"error": ...} while the rest still load.

    date: YYYY-MM-DD (default: today).
    """
    target = parse_day(date)
    return await fetch(lambda c: day.get_day(c, target))


@mcp.tool(title="Get daily summary", annotations=READS_GARMIN)
async def garmin_get_daily_summary(date: str | None = None) -> dict:
    """Every all-day wellness total for one date: steps, distance, floors,
    total/active/BMR calories, intensity minutes, heart rate, stress, body
    battery, SpO2, respiration, and time active/sedentary/asleep.

    date: YYYY-MM-DD (default: today).
    """
    target = parse_day(date)
    return await fetch(lambda c: daily_summary.get_daily_summary(c, target))


@mcp.tool(title="Get daily summaries", annotations=READS_GARMIN)
async def garmin_get_daily_summaries(
    start: str | None = None, end: str | None = None
) -> dict:
    """Daily wellness summaries across a date range, grouped per day (movement,
    calories, heart rate, intensity minutes, stress, body battery, hydration,
    respiration, pulse ox, jet lag). About 1-2 KB per day, so for a long
    trend in one metric prefer garmin_get_steps, garmin_get_stress, or
    garmin_get_sleep_summaries.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Ranges
    over a year are fetched in yearly requests.
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: daily_summary.get_daily_summaries(c, first, last))


@mcp.tool(title="Get steps", annotations=READS_GARMIN)
async def garmin_get_steps(start: str | None = None, end: str | None = None) -> dict:
    """Daily total steps, distance (meters), and step goal.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Any
    length works; long ranges are fetched 28 days at a time.
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: daily_summary.get_stats(c, "steps", first, last))


@mcp.tool(title="Get stress", annotations=READS_GARMIN)
async def garmin_get_stress(start: str | None = None, end: str | None = None) -> dict:
    """Daily overall stress level (0-100) and seconds spent in high, medium,
    low, and rest stress.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Any
    length works; long ranges are fetched 28 days at a time.
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: daily_summary.get_stats(c, "stress", first, last))


@mcp.tool(title="Get hydration", annotations=READS_GARMIN)
async def garmin_get_hydration(
    start: str | None = None, end: str | None = None
) -> dict:
    """Daily water intake, goal, estimated sweat loss, and intake logged during
    activities, all in mL.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Any
    length works; long ranges are fetched 31 days at a time.
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: daily_summary.get_stats(c, "hydration", first, last))


@mcp.tool(title="Get body battery", annotations=READS_GARMIN)
async def garmin_get_body_battery(
    start: str | None = None, end: str | None = None, chunks: int | None = None
) -> dict:
    """Daily Body Battery: amount charged and drained, plus the events that
    moved it (sleep, activities, stress) with Garmin's feedback.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Any
    length works; long ranges are fetched 31 days at a time.
    chunks: split each day into this many intervals (e.g. 24 for hourly) and
    include each interval's lowest and highest level. Omitted, the
    every-few-minutes readings are left out to keep the response small.
    """
    first, last = parse_range(start, end)
    return await fetch(
        lambda c: wellness.get_body_battery(c, first, last, chunks=chunks)
    )


@mcp.tool(title="Get heart rate", annotations=READS_GARMIN)
async def garmin_get_heart_rate(
    date: str | None = None, include_samples: bool = False
) -> dict:
    """Resting, minimum, and maximum heart rate for a day, the 7-day resting
    average, and any abnormal high/low heart rate alerts.

    date: YYYY-MM-DD (default: today).
    include_samples: also return the all-day readings (large).
    """
    target = parse_day(date)
    return await fetch(
        lambda c: wellness.get_heart_rate(c, target, include_samples=include_samples)
    )


@mcp.tool(title="Get SpO2", annotations=READS_GARMIN)
async def garmin_get_spo2(
    date: str | None = None, include_samples: bool = False
) -> dict:
    """Blood oxygen (pulse ox) for a day: average, lowest, latest, sleep
    average, 7-day average, hourly averages, and altitude acclimation.

    date: YYYY-MM-DD (default: today).
    include_samples: also return every individual reading (large).
    """
    target = parse_day(date)
    return await fetch(
        lambda c: wellness.get_spo2(c, target, include_samples=include_samples)
    )


@mcp.tool(title="Get wellness activities", annotations=READS_GARMIN)
async def garmin_get_wellness_activities(
    start: str | None = None, end: str | None = None
) -> dict:
    """Wellness activities recorded by the device, each with its type,
    start and end time, per-metric summary values, and time in zones. Regular
    workouts like runs and rides are in garmin_search_activities instead.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: wellness.get_wellness_activities(c, first, last))


@mcp.tool(title="Get sleep", annotations=READS_GARMIN)
async def garmin_get_sleep(date: str | None = None) -> dict:
    """The full sleep record for the night ending on date: sleep score and its
    components, deep/light/REM/awake seconds, start and end times, overnight
    heart rate, SpO2, respiration, sleep stress, naps, and Garmin's feedback.

    date: YYYY-MM-DD, the morning you woke up (default: today, i.e. last night).
    """
    target = parse_day(date)
    return await fetch(lambda c: sleep.get_sleep(c, target))


@mcp.tool(title="Get sleep summaries", annotations=READS_GARMIN)
async def garmin_get_sleep_summaries(
    start: str | None = None, end: str | None = None
) -> dict:
    """Nightly sleep records across a date range, same fields as
    garmin_get_sleep. Use it for sleep trends.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today). Any
    length works; long ranges are fetched 31 days at a time.
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: sleep.get_sleep_summaries(c, first, last))


@mcp.tool(title="Get HRV night", annotations=READS_GARMIN)
async def garmin_get_hrv(date: str | None = None) -> dict:
    """One night of heart-rate variability: the summary (last-night average,
    5-minute high, weekly average, baseline band, status) plus every reading
    taken during sleep.

    date: YYYY-MM-DD, the morning you woke up (default: today).
    """
    target = parse_day(date)
    return await fetch(lambda c: hrv.get_hrv(c, target))


@mcp.tool(title="Get HRV summaries", annotations=READS_GARMIN)
async def garmin_get_hrv_summaries(
    start: str | None = None, end: str | None = None
) -> dict:
    """Nightly HRV summaries across a date range: last-night average, weekly
    average, baseline band, status, and Garmin's feedback.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: hrv.get_hrv_summaries(c, first, last))


@mcp.tool(title="Get weight", annotations=READS_GARMIN)
async def garmin_get_weight(
    start: str | None = None, end: str | None = None, include_all: bool = False
) -> dict:
    """Daily weight summaries over a range, the range average, and the nearest
    weigh-ins before and after it (handy when the range itself has none). Weights are in grams; body composition
    (BMI, body fat %, muscle and bone mass) appears when a smart scale
    recorded it.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    include_all: list every weigh-in per day with its time and body
    composition, not just the latest.
    """
    first, last = parse_range(start, end)
    return await fetch(
        lambda c: weight.get_weight(c, first, last, include_all=include_all)
    )


@mcp.tool(title="Get weight goals", annotations=READS_GARMIN)
async def garmin_get_weight_goals(
    start: str | None = None, end: str | None = None
) -> dict:
    """Weight goals in effect during a date range and their target ranges.

    start, end: YYYY-MM-DD inclusive (default: the 7 days ending today).
    """
    first, last = parse_range(start, end)
    return await fetch(lambda c: weight.get_weight_goals(c, first, last))


@mcp.tool(title="Get food log", annotations=READS_GARMIN)
async def garmin_get_food_log(
    date: str | None = None,
    meal_id: int | None = None,
    include_goals: bool = True,
    include_nutrition: bool = True,
    include_media: bool = False,
) -> dict:
    """Foods logged in Garmin Connect's nutrition tracker for a day, with
    serving sizes, calories and nutrients consumed, nutrition goals, and a
    per-meal breakdown.

    date: YYYY-MM-DD (default: today).
    meal_id: limit to one meal; ids appear in mealDetails of an unfiltered call.
    include_media: also return logged food photos.
    """
    target = parse_day(date)
    return await fetch(
        lambda c: nutrition.get_food_log(
            c,
            target,
            meal_id=meal_id,
            include_goals=include_goals,
            include_nutrition=include_nutrition,
            include_media=include_media,
        )
    )


@mcp.tool(title="Search activities", annotations=READS_GARMIN)
async def garmin_search_activities(
    start: str | None = None,
    end: str | None = None,
    search: str | None = None,
    activity_type: str | None = None,
    activity_subtype: str | None = None,
    excluded_activity_subtypes: list[str] | None = None,
    event_type: str | None = None,
    favorite: bool | None = None,
    exclude_children: bool = True,
    sort_by: str | None = None,
    sort_order: Literal["asc", "desc"] | None = None,
    min_distance: int | None = None,
    max_distance: int | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
    min_elapsed_duration: int | None = None,
    max_elapsed_duration: int | None = None,
    min_elevation: int | None = None,
    max_elevation: int | None = None,
    min_avg_power: int | None = None,
    north: float | None = None,
    south: float | None = None,
    east: float | None = None,
    west: float | None = None,
    min_max_depth: int | None = None,
    max_max_depth: int | None = None,
    deco_dive: bool | None = None,
    min_bottom_time: int | None = None,
    max_bottom_time: int | None = None,
    required_fields: list[str] | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Recorded activities (runs, rides, swims, strength, dives, ...), newest
    first, with name, type, start time, distance, duration, pace/speed, HR,
    power, cadence, calories, elevation, and training effect. Pass an
    activityId to garmin_get_activity for splits and full detail.

    All filters are optional and combine:
    start, end: YYYY-MM-DD, by the activity's local start date.
    search: text in the activity name or description.
    activity_type: parent type key, e.g. running, cycling, swimming,
    strength_training, hiking, walking. activity_subtype: a child key such as
    trail_running or indoor_cycling. excluded_activity_subtypes: child keys to
    leave out.
    event_type: race, training, recreation, fitness, specialEvent, or
    uncategorized. favorite: true for favorites only, false for non-favorites.
    exclude_children: hide individual legs of multisport activities.
    sort_by: a field such as distance, duration, or name (default: start time).
    sort_order: asc or desc (default desc).
    min_/max_distance (meters), min_/max_duration (timer seconds),
    min_/max_elapsed_duration (seconds including pauses), min_/max_elevation
    (gain, meters), min_avg_power (watts).
    north, south, east, west: a bounding box in decimal degrees around the
    start location; give all four or none.
    Dives: min_/max_max_depth (centimeters), deco_dive, min_/max_bottom_time
    (seconds).
    required_fields: activity fields that must be present, e.g. avgPower.
    limit, offset: page through results (each activity is about 3-4 KB).
    """
    first, last = None, None
    if start is not None or end is not None:
        first, last = parse_range(start, end)
    filters = activities.ActivitySearch(
        start=first,
        end=last,
        search=search,
        activity_type=activity_type,
        activity_subtype=activity_subtype,
        excluded_activity_subtypes=tuple(excluded_activity_subtypes or ()),
        event_type=event_type,
        favorite=favorite,
        exclude_children=exclude_children,
        sort_by=sort_by,
        sort_order=sort_order,
        min_distance=min_distance,
        max_distance=max_distance,
        min_duration=min_duration,
        max_duration=max_duration,
        min_elapsed_duration=min_elapsed_duration,
        max_elapsed_duration=max_elapsed_duration,
        min_elevation=min_elevation,
        max_elevation=max_elevation,
        min_avg_power=min_avg_power,
        start_area=activities.bounding_box(north, south, east, west),
        min_max_depth=min_max_depth,
        max_max_depth=max_max_depth,
        deco_dive=deco_dive,
        min_bottom_time=min_bottom_time,
        max_bottom_time=max_bottom_time,
        required_fields=tuple(required_fields or ()),
    )
    return await fetch(
        lambda c: activities.search_activities(c, filters, limit=limit, offset=offset)
    )


@mcp.tool(title="Get activity", annotations=READS_GARMIN)
async def garmin_get_activity(activity_id: int) -> dict:
    """Full detail for one activity: summary metrics (distance, time, pace,
    HR, power, cadence, elevation, training effect, calories), device and
    location metadata, and split/lap summaries.

    activity_id: activityId from garmin_search_activities or garmin_get_day.
    """
    return await fetch(lambda c: activities.get_activity(c, activity_id))


@mcp.tool(title="Get activity workouts", annotations=READS_GARMIN)
async def garmin_get_activity_workouts(activity_id: int) -> dict:
    """The structured workout(s) followed during an activity, step by step
    with targets.

    activity_id: activityId from garmin_search_activities or garmin_get_day.
    """
    return await fetch(lambda c: activities.get_activity_workouts(c, activity_id))


@mcp.tool(title="Download activity file", annotations=SAVES_LOCAL_FILE)
async def garmin_download_activity(
    activity_id: int, directory: str | None = None
) -> dict:
    """Download an activity's original file (a ZIP, usually holding a .fit)
    and save it on the machine running this server as
    activity-<activity_id>.zip, replacing any earlier download. Returns the
    saved path, size, and the files inside.

    activity_id: activityId from garmin_search_activities.
    directory: where to save (default: GARMIN_MCP_DOWNLOAD_DIR, else a garmin
    folder in the Downloads directory).
    """
    target = config.download_dir()
    if directory is not None:
        target = Path(directory).expanduser()
    return await fetch(lambda c: activities.download_activity(c, activity_id, target))


@mcp.tool(title="Get profile settings", annotations=READS_GARMIN)
async def garmin_get_profile() -> dict:
    """Profile settings: display name, measurement system and display formats,
    time zone, hydration units and containers, and preferred training days.
    Check measurementSystem before converting units for the user."""
    return await fetch(profile.get_settings)


@mcp.tool(title="Get heart rate zones", annotations=READS_GARMIN)
async def garmin_get_heart_rate_zones(generate_defaults: bool = True) -> dict:
    """Heart rate zone floors per sport, with the training method and the
    resting, max, and lactate threshold heart rates the zones were built on.

    generate_defaults: return Garmin's default zones when none are configured.
    """
    return await fetch(
        lambda c: profile.get_heart_rate_zones(c, generate_defaults=generate_defaults)
    )


@mcp.tool(title="Get fitness age", annotations=READS_GARMIN)
async def garmin_get_fitness_age(
    date: str | None = None, full_history_scan: bool = True
) -> dict:
    """Fitness age versus chronological age as of a date, the achievable
    fitness age, and the components behind it (vigorous days and minutes,
    resting heart rate, BMI or body fat %), or the reason none is available.

    date: YYYY-MM-DD (default: today).
    full_history_scan: search all history for the latest value; false limits
    it to the 28 days before date.
    """
    target = parse_day(date)
    return await fetch(
        lambda c: profile.get_fitness_age(
            c, target, full_history_scan=full_history_scan
        )
    )


@mcp.tool(title="Get menstrual cycle", annotations=READS_GARMIN)
async def garmin_get_menstrual_cycle(date: str | None = None) -> dict:
    """Menstrual cycle summary as of a date: current phase, day in cycle, days
    until the next phase, period length, fertile window, predicted ovulation
    and cycle length, and pregnancy details when tracking a pregnancy.

    date: YYYY-MM-DD (default: today).
    """
    target = parse_day(date)
    return await fetch(lambda c: womens_health.get_cycle_summary(c, target))


@mcp.tool(title="Get menstrual cycle day", annotations=READS_GARMIN)
async def garmin_get_menstrual_day(
    date: str | None = None,
    today: str | None = None,
    reduced: bool = False,
    skip_baby_movement: bool = False,
    include_analysis: bool = False,
) -> dict:
    """One day in detail: logged symptoms, flow, mood, and other entries, that
    day's cycle summary, and weekly weight goal ranges during pregnancy.

    date: YYYY-MM-DD (default: today).
    today: the reference date for predictions (default: today).
    reduced: return a lighter response.
    skip_baby_movement: leave out kick counts.
    include_analysis: add Garmin's cycle analysis.
    """
    target = parse_day(date)
    reference = parse_day(today)
    return await fetch(
        lambda c: womens_health.get_cycle_day(
            c,
            target,
            today=reference,
            reduced=reduced,
            skip_baby_movement=skip_baby_movement,
            include_analysis=include_analysis,
        )
    )
