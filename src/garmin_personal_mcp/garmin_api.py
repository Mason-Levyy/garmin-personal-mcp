import datetime
from collections.abc import Callable, Iterator, Sequence
from typing import Any

QueryValue = str | int | float | list[str]


def query(**values: Any) -> dict[str, QueryValue]:
    """Drops unset values. Booleans go out lowercase because requests would
    send Python's "True"."""
    params = {}
    for name, value in values.items():
        if value is None or value == []:
            continue
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, datetime.date):
            value = value.isoformat()
        params[name] = value
    return params


def windows(
    start: datetime.date, end: datetime.date, max_days: int
) -> Iterator[tuple[datetime.date, datetime.date]]:
    window_start = start
    while window_start <= end:
        window_end = min(window_start + datetime.timedelta(days=max_days - 1), end)
        yield window_start, window_end
        window_start = window_end + datetime.timedelta(days=1)


def in_windows(
    start: datetime.date,
    end: datetime.date,
    max_days: int,
    fetch: Callable[[datetime.date, datetime.date], list | None],
) -> list:
    """Splits a range that exceeds an endpoint's documented maximum into
    consecutive requests and concatenates the rows."""
    rows = []
    for first, last in windows(start, end, max_days):
        rows.extend(fetch(first, last) or [])
    return rows


def without(record: Any, fields: Sequence[str]) -> Any:
    if isinstance(record, list):
        return [without(item, fields) for item in record]
    if not isinstance(record, dict):
        return record
    return {key: value for key, value in record.items() if key not in fields}
