import datetime

from .garmin_api import query


def get_settings(client) -> dict | None:
    return client.get("/userprofile-service/userprofile/settings")


def get_heart_rate_zones(client, *, generate_defaults: bool = True) -> list | None:
    return client.get(
        "/biometric-service/heartRateZones/v2",
        params=query(generateDefaults=generate_defaults),
    )


def get_fitness_age(
    client, day: datetime.date, *, full_history_scan: bool = True
) -> list | None:
    return client.get(
        f"/fitnessage-service/fitnessage/v2/{day}",
        params=query(fullHistoryScan=full_history_scan),
    )
