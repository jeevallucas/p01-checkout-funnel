"""Run the shared funnel queries in DuckDB against small hand-built sessions."""

import duckdb
import pytest

from checkout_funnel.funnel import FUNNEL_STEPS
from checkout_funnel.sql_files import shared_query


def session_events(session_key, device_category, *timed_steps):
    """Rows for one session; timed_steps are (step_name, event_at) pairs."""
    return [(session_key, step, event_at, device_category) for step, event_at in timed_steps]


def full_path(session_key, device_category):
    return session_events(
        session_key, device_category, *[(step, 10 * i) for i, step in enumerate(FUNNEL_STEPS)]
    )


def run_shared(query_name, rows):
    connection = duckdb.connect()
    connection.execute(
        "create table session_step_event "
        "(session_key varchar, step_name varchar, event_at bigint, device_category varchar)"
    )
    connection.executemany("insert into session_step_event values (?, ?, ?, ?)", rows)
    query = shared_query(query_name, session_step_event="session_step_event")
    result = connection.execute(query)
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def step_pairs(rows):
    """{(device, step): (entered, reached)} from funnel_step_sessions."""
    return {
        (row["device_category"], row["step_name"]): (
            row["sessions_entered"],
            row["sessions_reached"],
        )
        for row in run_shared("funnel_step_sessions", rows)
    }


def test_a_session_through_every_step_enters_and_reaches_each_pair_once():
    pairs = step_pairs(full_path("s1", "mobile"))
    assert pairs == {("mobile", step): (1, 1) for step in FUNNEL_STEPS[1:]}


def test_event_order_is_ignored():
    rows = session_events(
        "s1", "mobile", ("session_start", 0), ("add_shipping_info", 5), ("begin_checkout", 9)
    )
    assert step_pairs(rows)[("mobile", "add_shipping_info")] == (1, 1)


def test_a_purchase_without_add_to_cart_still_counts_in_the_later_pairs():
    rows = [row for row in full_path("s1", "desktop") if row[1] != "add_to_cart"]
    pairs = step_pairs(rows)
    assert pairs[("desktop", "add_to_cart")] == (1, 0)
    assert pairs[("desktop", "begin_checkout")] == (0, 0)
    assert pairs[("desktop", "purchase")] == (1, 1)


def test_repeated_events_count_the_session_once():
    rows = session_events(
        "s1", "mobile", ("session_start", 0), ("view_item", 1), ("view_item", 2), ("view_item", 3)
    )
    assert step_pairs(rows)[("mobile", "view_item")] == (1, 1)


def test_a_session_that_leaves_after_viewing_counts_as_entered_but_not_reached():
    rows = session_events("s1", "tablet", ("session_start", 0), ("view_item", 4))
    pairs = step_pairs(rows)
    assert pairs[("tablet", "view_item")] == (1, 1)
    assert pairs[("tablet", "add_to_cart")] == (1, 0)


def test_devices_are_counted_separately_and_sessions_add_up():
    rows = (
        full_path("m1", "mobile")
        + session_events("m2", "mobile", ("session_start", 0), ("view_item", 3))
        + full_path("d1", "desktop")
    )
    pairs = step_pairs(rows)
    assert pairs[("mobile", "view_item")] == (2, 2)
    assert pairs[("mobile", "add_to_cart")] == (2, 1)
    assert pairs[("desktop", "purchase")] == (1, 1)


def test_order_check_counts_contradictions_in_the_sample():
    rows = (
        session_events("s1", "mobile", ("add_shipping_info", 1), ("begin_checkout", 2))
        + session_events("s2", "mobile", ("begin_checkout", 1), ("add_shipping_info", 2))
        + session_events("s3", "desktop", ("view_item", 1), ("purchase", 5))
        + full_path("s4", "desktop")
    )
    (check,) = run_shared("checkout_order_check", rows)
    assert check == {
        "checkout_sessions": 3,
        "shipping_before_checkout": 1,
        "purchase_sessions": 2,
        "purchases_without_add_to_cart": 1,
        "purchases_without_view_item": 0,
    }


def test_shared_query_names_the_missing_table():
    with pytest.raises(ValueError, match="session_step_event"):
        shared_query("funnel_step_sessions")
