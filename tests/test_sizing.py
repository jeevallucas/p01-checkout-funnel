import pandas as pd
import pytest

from checkout_funnel.sizing import (
    coupon_holdout_test,
    mobile_only_upper_bound,
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


def test_mobile_upper_bound_closes_half_of_the_worst_deficit_the_interval_allows():
    mobile_gap = pd.DataFrame(
        {
            "step_name": ["add_payment_info", "purchase"],
            "mobile_sessions_entered": [2000, 1000],
            "gap_low": [-0.02, 0.01],
        }
    )
    table = mobile_only_upper_bound(mobile_gap, STEP_PURCHASE, ORDER_VALUE)
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
    table = payment_step_test(step_conversion, STEP_PURCHASE, ORDER_VALUE, export_days=92)
    # Desktop 6000 x 0.01 x 0.75 x $80 plus mobile 4000 x 0.01 x 0.70 x $60.
    assert table["revenue_per_point_usd"].iloc[0] == pytest.approx(3600 + 1680)
    assert table["baseline_conversion"].iloc[0] == pytest.approx(0.6)
    lifts = table["detectable_lift_points"].tolist()
    assert lifts == sorted(lifts, reverse=True)
    assert table["sessions_per_arm"].iloc[0] == int(10000 / 92 * 7 * 4 / 2)


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
