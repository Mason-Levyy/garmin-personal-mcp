import datetime

from .garmin_api import in_windows, query

# Garmin's limit for this endpoint; it isn't in the Swagger reference.
VO2_MAX_MAX_DAYS = 366


def get_settings(client) -> dict | None:
    return client.get("/userprofile-service/userprofile/settings")


def get_heart_rate_zones(client, *, generate_defaults: bool = True) -> list | None:
    return client.get(
        "/biometric-service/heartRateZones/v2",
        params=query(generateDefaults=generate_defaults),
    )


def get_vo2_max(
    client, start: datetime.date, end: datetime.date, *, sport: list[str] | None = None
) -> list:
    def fetch(first, last):
        return client.get(
            f"/metrics-service/metrics/maxmet/daily/{first}/{last}",
            params=query(sport=sport),
        )

    return in_windows(start, end, VO2_MAX_MAX_DAYS, fetch)


def get_fitness_age(
    client, day: datetime.date, *, full_history_scan: bool = True
) -> list | None:
    return client.get(
        f"/fitnessage-service/fitnessage/v2/{day}",
        params=query(fullHistoryScan=full_history_scan),
    )
