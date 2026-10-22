import datetime

from .garmin_api import in_windows, query

SUMMARIES_MAX_DAYS = 31


def get_sleep(client, day: datetime.date) -> dict | None:
    return client.get("/sleep-service/sleep/dailySleep", params=query(date=day))


def get_sleep_summaries(client, start: datetime.date, end: datetime.date) -> list:
    return in_windows(
        start,
        end,
        SUMMARIES_MAX_DAYS,
        lambda first, last: client.get(
            "/sleep-service/sleep/dailySleepSummariesByDate",
            params=query(startDate=first, endDate=last),
        ),
    )
