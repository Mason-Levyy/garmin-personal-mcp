import datetime

from .garmin_api import query


def get_weight(
    client, start: datetime.date, end: datetime.date, *, include_all: bool = False
) -> dict | None:
    return client.get(
        f"/weight-service/weight/range/{start}/{end}",
        params=query(includeAll=include_all),
    )


def get_weight_goals(client, start: datetime.date, end: datetime.date) -> dict | None:
    return client.get(f"/goal-service/goal/user/effective/weightgoal/{start}/{end}")
