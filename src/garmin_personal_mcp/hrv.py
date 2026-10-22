import datetime


def get_hrv(client, day: datetime.date) -> dict | None:
    return client.get(f"/hrv-service/hrv/{day}")


def get_hrv_summaries(client, start: datetime.date, end: datetime.date) -> dict | None:
    return client.get(f"/hrv-service/hrv/daily/{start}/{end}")
