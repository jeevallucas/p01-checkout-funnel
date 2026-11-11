import pandas as pd
import pytest

from checkout_funnel.sizing import (
    coupon_holdout_test,
    january_pace,
    mobile_catch_up_ceiling,
    order_value_by_device,
    payment_step_test,
)

ORDER_VALUE = pd.DataFrame(
    {
        "device_category": ["desktop", "mobile"],
        "orders": [100, 50],
        "revenue_usd": [8000.0, 3000.0],
        "zero_revenue_orders": [0, 0],
    }
)

STEP_PURCHASE = pd.DataFrame(
    {
        "device_category": ["mobile", "mobile", "desktop"],
        "step_name": ["add_payment_info", "purchase", "add_payment_info"],
        "sessions_with_step": [1000, 700, 2000],
        "sessions_purchased": [700, 700, 1500],
    }
)


def test_order_value_divides_revenue_by_orders():
    assert order_value_by_device(ORDER_VALUE) == {"desktop": 80.0, "mobile": 60.0}


def test_mobile_catch_up_closes_half_of_the_worst_deficit_the_interval_allows():
    mobile_gap = pd.DataFrame(
        {
            "step_name": ["add_payment_info", "purchase"],
            "mobile_sessions_entered": [2000, 1000],
            "gap_low": [-0.02, 0.01],
        }
    )
    table = mobile_catch_up_ceiling(mobile_gap, STEP_PURCHASE, ORDER_VALUE)
    payment = table[table["step_name"] == "add_payment_info"].iloc[0]
    # 2000 sessions x 1 point x 70% purchase x $60.
    assert payment["extra_sessions_reaching_step"] == pytest.approx(20)
    assert payment["extra_revenue_usd"] == pytest.approx(20 * 0.7 * 60)
    # An interval entirely above zero allows no mobile deficit, so there is nothing to recover.
    purchase = table[table["step_name"] == "purchase"].iloc[0]
    assert purchase["extra_revenue_usd"] == 0
    assert table.iloc[0]["step_name"] == "add_payment_info"


def test_payment_step_value_per_point_sums_devices_and_longer_tests_detect_less():
    step_conversion = pd.DataFrame(
        {
            "device_category": ["desktop", "mobile"],
            "step_name": ["add_payment_info", "add_payment_info"],
            "sessions_entered": [6000, 4000],
            "sessions_reached": [3600, 2400],
        }
    )
    paces = {"average": 1.0, "quiet": 0.5}
    table = payment_step_test(step_conversion, STEP_PURCHASE, ORDER_VALUE, 92, paces)
    rows = table.set_index(["scope", "traffic_pace", "test_weeks"])
    everyone = rows.loc[("all devices", "average")]
    # Desktop 6000 x 0.01 x 0.75 x $80 plus mobile 4000 x 0.01 x 0.70 x $60.
    assert everyone["revenue_per_point_usd"].iloc[0] == pytest.approx(3600 + 1680)
    assert everyone["baseline_conversion"].iloc[0] == pytest.approx(0.6)
    assert everyone.loc[4, "sessions_per_arm"] == int(10000 / 92 * 7 * 4 / 2)
    lifts = everyone["detectable_lift_points"].tolist()
    assert lifts == sorted(lifts, reverse=True)
    # Mobile only: the same step and lift on 40% of the sessions.
    mobile = rows.loc[("mobile only", "average")]
    assert mobile["revenue_per_point_usd"].iloc[0] == pytest.approx(1680)
    assert (mobile["detectable_lift_points"] > everyone["detectable_lift_points"]).all()
    # Half the traffic needs a larger lift to be detected in the same weeks.
    quiet = rows.loc[("all devices", "quiet")]
    assert (quiet["detectable_lift_points"] > everyone["detectable_lift_points"]).all()


def test_january_pace_compares_january_with_the_whole_export():
    daily = pd.DataFrame(
        {
            "event_day": ["2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02"],
            "purchase_events": [90, 90, 30, 30],
        }
    )
    assert january_pace(daily) == pytest.approx(30 / 60)


def test_coupon_holdout_reports_days_of_buyers_needed():
    difference = pd.DataFrame(
        {"window_days": [30], "no_coupon_repeat_rate": [0.05], "coupon_repeat_rate": [0.06]}
    )
    table = coupon_holdout_test(difference, buyers_per_day=40.0, holdout_days=90)
    row = table.iloc[0]
    per_arm = row["buyers_per_arm_for_observed_difference"]
    assert per_arm > 1000
    assert row["days_of_first_time_buyers_needed"] == pytest.approx(2 * per_arm / 40)
    # 90 days at 40 buyers a day, split in two, is too few to see a 1-point difference.
    assert row["holdout_buyers_per_arm"] == 1800
    assert row["holdout_detectable_difference_points"] > 1.0
    assert row["buyers_per_day"] == 40.0
