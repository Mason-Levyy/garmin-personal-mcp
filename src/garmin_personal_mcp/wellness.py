import datetime

from .garmin_api import in_windows, query, without

BODY_BATTERY_MAX_DAYS = 31

HEART_RATE_SAMPLES = ("heartRateValues", "heartRateValueDescriptors")
SPO2_SAMPLES = ("spO2SingleValues", "spO2SingleValuesDescriptorList")
BODY_BATTERY_SAMPLES = (
    "bodyBatteryValuesArray",
    "bodyBatteryValueDescriptorDTOList",
)


def get_body_battery(
    client, start: datetime.date, end: datetime.date, *, chunks: int | None = None
) -> list:
    """Without chunks, the value array is every reading of the day; with chunks
    it is the low and high of each interval, which is what the caller asked
    for, so only the full-resolution form is dropped."""

    def fetch(first, last):
        return client.get(
            "/wellness-service/wellness/bodyBattery/reports/daily",
            params=query(startDate=first, endDate=last, chunks=chunks),
        )

    reports = in_windows(start, end, BODY_BATTERY_MAX_DAYS, fetch)
    if chunks is None:
        return without(reports, BODY_BATTERY_SAMPLES)
    return reports


def get_heart_rate(
    client, day: datetime.date, *, include_samples: bool = False
) -> dict | None:
    record = client.get(
        "/wellness-service/wellness/dailyHeartRate", params=query(date=day)
    )
    if include_samples:
        return record
    return without(record, HEART_RATE_SAMPLES)


def get_spo2(
    client, day: datetime.date, *, include_samples: bool = False
) -> dict | None:
    record = client.get(f"/wellness-service/wellness/daily/spo2acclimation/{day}")
    if include_samples:
        return record
    return without(record, SPO2_SAMPLES)


def get_wellness_activities(
    client, start: datetime.date, end: datetime.date
) -> list | None:
    return client.get(f"/wellnessactivity-service/activity/summary/range/{start}/{end}")
