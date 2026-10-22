import datetime
from collections.abc import Callable

from garmin_personal_api import HttpError

from . import activities, daily_summary, hrv, sleep, wellness
from .garmin_client import UNAUTHORIZED

DAY_ACTIVITY_LIMIT = 20


def day_sections(day: datetime.date) -> dict[str, Callable]:
    return {
        "summary": lambda c: daily_summary.get_daily_summary(c, day),
        "sleep": lambda c: sleep.get_sleep(c, day),
        "hrv": lambda c: hrv.get_hrv_summaries(c, day, day),
        "body_battery": lambda c: wellness.get_body_battery(c, day, day),
        "stress": lambda c: daily_summary.get_stats(c, "stress", day, day),
        "activities": lambda c: activities.search_activities(
            c,
            activities.ActivitySearch(start=day, end=day),
            limit=DAY_ACTIVITY_LIMIT,
            offset=0,
        ),
    }


def get_day(client, day: datetime.date) -> dict:
    """Garmin answers 4xx for data that doesn't exist yet (e.g. today's HRV
    before you've slept), so one missing section shouldn't sink the rest. A 401
    still propagates so garmin_client.call can retry with a fresh token."""
    record = {"date": day.isoformat()}
    for name, read in day_sections(day).items():
        try:
            record[name] = read(client)
        except HttpError as exc:
            if exc.status_code == UNAUTHORIZED:
                raise
            record[name] = {"error": str(exc)}
    return record
