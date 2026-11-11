"""Run the shared funnel query in DuckDB against small hand-built sessions."""

import duckdb
import pytest

from checkout_funnel.sql_files import shared_query

FUNNEL_STEPS = [
    "session_start",
    "view_item",
    "add_to_cart",
    "begin_checkout",
    "add_shipping_info",
    "add_payment_info",
    "purchase",
]


def session_events(session_key, device_category, *timed_steps):
    """Rows for one session; timed_steps are (step_name, event_at) pairs."""
    return [(session_key, step, event_at, device_category) for step, event_at in timed_steps]


def full_path(session_key, device_category):
    return session_events(
        session_key, device_category, *[(step, 10 * i) for i, step in enumerate(FUNNEL_STEPS)]
    )


def funnel_counts(rows):
    connection = duckdb.connect()
    connection.execute(
        "create table session_step_event "
        "(session_key varchar, step_name varchar, event_at bigint, device_category varchar)"
    )
    connection.executemany("insert into session_step_event values (?, ?, ?, ?)", rows)
    query = shared_query("funnel_step_sessions", session_step_event="session_step_event")
    return {
        (device, step): sessions
        for device, _, step, sessions in connection.execute(query).fetchall()
    }


def test_a_session_through_every_step_counts_once_at_each_step():
    counts = funnel_counts(full_path("s1", "mobile"))
    assert counts == {("mobile", step): 1 for step in FUNNEL_STEPS}


def test_add_to_cart_before_viewing_the_item_does_not_count():
    rows = session_events(
        "s1", "mobile", ("session_start", 0), ("add_to_cart", 5), ("view_item", 9)
    )
    counts = funnel_counts(rows)
    assert counts[("mobile", "view_item")] == 1
    assert ("mobile", "add_to_cart") not in counts


def test_a_later_repeat_of_the_step_satisfies_the_order():
    rows = session_events(
        "s1",
        "mobile",
        ("session_start", 0),
        ("add_to_cart", 5),
        ("view_item", 9),
        ("add_to_cart", 12),
    )
    assert funnel_counts(rows)[("mobile", "add_to_cart")] == 1


def test_skipping_a_step_stops_the_session_there_even_if_it_buys():
    rows = [row for row in full_path("s1", "desktop") if row[1] != "add_shipping_info"]
    counts = funnel_counts(rows)
    assert counts[("desktop", "begin_checkout")] == 1
    for later_step in ("add_shipping_info", "add_payment_info", "purchase"):
        assert ("desktop", later_step) not in counts


def test_a_session_without_session_start_is_not_in_the_funnel():
    rows = [row for row in full_path("s1", "mobile") if row[1] != "session_start"]
    assert funnel_counts(rows) == {}


def test_events_with_equal_timestamps_count_as_in_order():
    rows = session_events(
        "s1", "tablet", ("session_start", 0), ("view_item", 0), ("add_to_cart", 0)
    )
    counts = funnel_counts(rows)
    assert counts[("tablet", "add_to_cart")] == 1


def test_devices_are_counted_separately_and_sessions_add_up():
    rows = (
        full_path("m1", "mobile")
        + session_events("m2", "mobile", ("session_start", 0), ("view_item", 3))
        + full_path("d1", "desktop")
    )
    counts = funnel_counts(rows)
    assert counts[("mobile", "session_start")] == 2
    assert counts[("mobile", "view_item")] == 2
    assert counts[("mobile", "add_to_cart")] == 1
    assert counts[("desktop", "purchase")] == 1


def test_shared_query_names_the_missing_table():
    with pytest.raises(ValueError, match="session_step_event"):
        shared_query("funnel_step_sessions")
