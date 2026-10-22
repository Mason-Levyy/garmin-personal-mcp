import datetime

from .garmin_api import query


def get_cycle_summary(client, day: datetime.date) -> dict | None:
    return client.get(f"/periodichealth-service/menstrualcycle/summary/{day}")


def get_cycle_day(
    client,
    day: datetime.date,
    *,
    today: datetime.date,
    reduced: bool = False,
    skip_baby_movement: bool = False,
    include_analysis: bool = False,
) -> dict | None:
    return client.get(
        f"/periodichealth-service/menstrualcycle/dayview/{day}",
        params=query(
            todayDate=today,
            reducedResponse=reduced,
            skipbm=skip_baby_movement,
            includeAnalysis=include_analysis,
        ),
    )
