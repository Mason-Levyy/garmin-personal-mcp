import datetime

from .garmin_api import in_windows, query

# Per-request range limits from Garmin's Personal API reference.
SUMMARIES_MAX_DAYS = 365
STATS_MAX_DAYS = {"steps": 28, "stress": 28, "hydration": 31}


def get_daily_summary(client, day: datetime.date) -> dict | None:
    return client.get(
        "/usersummary-service/usersummary/daily", params=query(calendarDate=day)
    )


def get_daily_summaries(
    client, start: datetime.date, end: datetime.date
) -> dict[str, list]:
    def fetch(first, last):
        page = client.get(
            "/usersummary-service/v2/dailysummaries",
            params=query(startDate=first, endDate=last),
        )
        return (page or {}).get("data")

    return {"data": in_windows(start, end, SUMMARIES_MAX_DAYS, fetch)}


def get_stats(client, metric: str, start: datetime.date, end: datetime.date) -> list:
    return in_windows(
        start,
        end,
        STATS_MAX_DAYS[metric],
        lambda first, last: client.get(
            f"/usersummary-service/stats/{metric}/daily/{first}/{last}"
        ),
    )
