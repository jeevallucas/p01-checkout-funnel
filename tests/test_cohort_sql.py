"""Run the shared repeat-purchase query in DuckDB against hand-built buyers.

The export runs from day 100 to day 200 here, so a 30-day window needs a first purchase on or
before day 170 and a 60-day window on or before day 140.
"""

import duckdb
import pandas as pd
import pytest

from checkout_funnel.cohorts import coupon_difference_table, repeat_rate_table
from checkout_funnel.sql_files import shared_query

BUYERS = [
    # user_key, first_touch_day, acquisition_medium
    ("repeats_after_15_days", 100, "organic"),
    ("buys_twice_same_day", 105, "organic"),
    ("repeats_after_45_days", 100, "direct"),
    ("first_buys_late", 150, "paid search"),
    ("first_seen_before_export", 90, "organic"),
    ("coupon_only_on_second_order", 100, "referral"),
    ("unknown_medium", 101, "unknown"),
    ("too_late_for_any_window", 120, "organic"),
    ("no_first_touch", None, "organic"),
]

PURCHASES = [
    # user_key, purchase_day, used_coupon
    ("repeats_after_15_days", 110, True),
    ("repeats_after_15_days", 125, False),
    ("buys_twice_same_day", 120, False),
    ("buys_twice_same_day", 120, False),
    ("repeats_after_45_days", 130, False),
    ("repeats_after_45_days", 175, False),
    ("first_buys_late", 160, False),
    ("first_buys_late", 185, False),
    ("first_seen_before_export", 110, False),
    ("first_seen_before_export", 115, False),
    ("coupon_only_on_second_order", 110, False),
    ("coupon_only_on_second_order", 112, True),
    ("unknown_medium", 140, False),
    ("too_late_for_any_window", 175, False),
    ("no_first_touch", 110, False),
    ("no_first_touch", 111, False),
]


def cohort_rows():
    connection = duckdb.connect()
    connection.execute(
        "create table buyer (user_key varchar, first_touch_day integer, acquisition_medium varchar)"
    )
    connection.execute(
        "create table purchase_event (user_key varchar, purchase_day integer, used_coupon boolean)"
    )
    connection.executemany("insert into buyer values (?, ?, ?)", BUYERS)
    connection.executemany("insert into purchase_event values (?, ?, ?)", PURCHASES)
    query = shared_query(
        "repeat_purchase_cohorts",
        purchase_event="purchase_event",
        buyer="buyer",
        export_first_day="100",
        export_last_day="200",
    )
    return connection.execute(query).df()


@pytest.fixture(scope="module")
def cohorts():
    return cohort_rows()


def counts(cohorts, split, segment, window_days):
    row = cohorts[
        (cohorts["split"] == split)
        & (cohorts["segment"] == segment)
        & (cohorts["window_days"] == window_days)
    ]
    if row.empty:
        return None
    return int(row["first_time_buyers"].iloc[0]), int(row["repeat_buyers"].iloc[0])


def test_only_buyers_whose_whole_window_fits_are_counted(cohorts):
    # 30 days: six eligible; "first_buys_late" fits 30 but not 60.
    assert counts(cohorts, "all", "all first-time buyers", 30) == (6, 3)
    assert counts(cohorts, "all", "all first-time buyers", 60) == (5, 3)


def test_same_day_second_order_is_not_a_repeat(cohorts):
    assert counts(cohorts, "acquisition medium", "organic", 30) == (2, 1)


def test_a_repeat_after_45_days_counts_only_in_the_60_day_window(cohorts):
    assert counts(cohorts, "acquisition medium", "direct", 30) == (1, 0)
    assert counts(cohorts, "acquisition medium", "direct", 60) == (1, 1)


def test_coupon_is_read_from_the_first_purchase_day_only(cohorts):
    assert counts(cohorts, "coupon at first purchase", "coupon", 30) == (1, 1)
    assert counts(cohorts, "coupon at first purchase", "no coupon", 30) == (5, 2)


def test_unknown_medium_stays_as_its_own_segment(cohorts):
    assert counts(cohorts, "acquisition medium", "unknown", 60) == (1, 0)


def test_buyers_first_seen_before_the_export_or_never_are_left_out(cohorts):
    # Five organic buyers: one first seen before the export, one with no first touch, and one
    # whose first purchase is too late for any window are not counted.
    assert counts(cohorts, "acquisition medium", "organic", 60) == (2, 1)


def test_a_segment_with_no_eligible_buyer_has_no_row(cohorts):
    assert counts(cohorts, "acquisition medium", "paid search", 60) is None


def test_rate_table_and_coupon_difference_use_the_counts(cohorts):
    rates = repeat_rate_table(cohorts)
    all_30 = rates[(rates["split"] == "all") & (rates["window_days"] == 30)].iloc[0]
    assert all_30["repeat_rate"] == pytest.approx(0.5)
    assert all_30["repeat_rate_low"] < 0.5 < all_30["repeat_rate_high"]
    difference = coupon_difference_table(cohorts)
    row_30 = difference[difference["window_days"] == 30].iloc[0]
    assert row_30["difference"] == pytest.approx(1.0 - 2 / 5)
    assert not row_30["difference_excludes_zero"]


def test_coupon_difference_needs_both_segments():
    only_coupon = pd.DataFrame(
        [
            {
                "split": "coupon at first purchase",
                "segment": "coupon",
                "window_days": 30,
                "first_time_buyers": 10,
                "repeat_buyers": 2,
            }
        ]
    )
    with pytest.raises(ValueError, match="needs both"):
        coupon_difference_table(only_coupon)


def test_order_value_counts_each_transaction_once_on_its_first_device():
    connection = duckdb.connect()
    connection.execute(
        "create table purchase_event (transaction_id varchar, device_category varchar, "
        "event_at bigint, revenue_usd double)"
    )
    connection.executemany(
        "insert into purchase_event values (?, ?, ?, ?)",
        [
            ("t1", "mobile", 1, 50.0),
            ("t1", "desktop", 2, 50.0),  # same order logged again from another device
            ("t2", "desktop", 3, 30.0),
            (None, "desktop", 4, 20.0),  # no usable ID: one order on its own
            (None, "desktop", 5, 0.0),
        ],
    )
    rows = connection.execute(shared_query("order_value", purchase_event="purchase_event")).df()
    by_device = rows.set_index("device_category")
    assert by_device.loc["mobile", "orders"] == 1
    assert by_device.loc["mobile", "revenue_usd"] == 50.0
    assert by_device.loc["desktop", "orders"] == 3
    assert by_device.loc["desktop", "revenue_usd"] == 50.0
    assert by_device.loc["desktop", "zero_revenue_orders"] == 1
