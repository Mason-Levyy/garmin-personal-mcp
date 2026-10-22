import datetime

from garmin_personal_mcp.garmin_api import in_windows, query, windows, without

D = datetime.date


def test_query_drops_unset_values_and_lowercases_booleans():
    assert query(a=None, b=True, c=False, d=0, e=[], f=["x", "y"]) == {
        "b": "true",
        "c": "false",
        "d": 0,
        "f": ["x", "y"],
    }


def test_query_formats_dates():
    assert query(startDate=D(2026, 10, 1)) == {"startDate": "2026-10-01"}


def test_windows_cover_the_range_without_gaps_or_overlap():
    spans = list(windows(D(2026, 1, 1), D(2026, 3, 1), 28))
    assert spans == [
        (D(2026, 1, 1), D(2026, 1, 28)),
        (D(2026, 1, 29), D(2026, 2, 25)),
        (D(2026, 2, 26), D(2026, 3, 1)),
    ]


def test_windows_single_day():
    assert list(windows(D(2026, 1, 1), D(2026, 1, 1), 28)) == [
        (D(2026, 1, 1), D(2026, 1, 1))
    ]


def test_windows_exactly_max_days_is_one_request():
    assert len(list(windows(D(2026, 1, 1), D(2026, 1, 28), 28))) == 1


def test_in_windows_concatenates_and_skips_empty_pages():
    pages = {D(2026, 1, 1): [1, 2], D(2026, 1, 3): None, D(2026, 1, 5): [3]}
    rows = in_windows(D(2026, 1, 1), D(2026, 1, 6), 2, lambda first, last: pages[first])
    assert rows == [1, 2, 3]


def test_without_strips_fields_from_dicts_and_lists():
    record = {"keep": 1, "drop": 2}
    assert without(record, ["drop"]) == {"keep": 1}
    assert without([record, record], ["drop"]) == [{"keep": 1}, {"keep": 1}]
    assert without(None, ["drop"]) is None
