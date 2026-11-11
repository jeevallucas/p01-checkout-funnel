"""Revenue at stake and test sizes for the memo, computed from the committed aggregate files.

All revenue is in the sample's US dollars over its 92 days. It describes this obfuscated sample,
not the real store, and every function states the assumption it adds.
"""

import pandas as pd

from checkout_funnel.conversion_stats import detectable_rate, sessions_per_arm

PAYMENT_STEP = "add_payment_info"


def order_value_by_device(order_value: pd.DataFrame) -> dict[str, float]:
    """Average order value per device: revenue over orders, each transaction ID counted once."""
    if (order_value["orders"] <= 0).any():
        raise ValueError(
            "cohort_order_value.csv has a device with no orders, so its order value is undefined; "
            "rerun `uv run pipeline cohorts` and check sql/shared/order_value.sql."
        )
    return dict(
        zip(
            order_value["device_category"],
            order_value["revenue_usd"] / order_value["orders"],
            strict=True,
        )
    )


def purchase_rate_by_step(step_purchase: pd.DataFrame) -> dict[tuple[str, str], float]:
    """Share of sessions with a step that also purchased, per (device, step)."""
    return {
        (row.device_category, row.step_name): row.sessions_purchased / row.sessions_with_step
        for row in step_purchase.itertuples()
    }


def mobile_only_upper_bound(
    mobile_gap: pd.DataFrame, step_purchase: pd.DataFrame, order_value: pd.DataFrame
) -> pd.DataFrame:
    """The most a mobile-only fix could add, per step, under the card's sizing rule.

    Assumption: the true mobile deficit is as large as the 95% interval allows (its lower bound),
    and a fix closes half of it. Each extra session reaching the step then buys at the rate
    sessions with that step already do, at the mobile average order value.
    """
    purchase_rate = purchase_rate_by_step(step_purchase)
    mobile_order_value = order_value_by_device(order_value)["mobile"]
    rows = []
    for gap in mobile_gap.itertuples():
        worst_deficit = max(0.0, -gap.gap_low)
        extra_sessions = gap.mobile_sessions_entered * worst_deficit / 2
        extra_revenue = (
            extra_sessions * purchase_rate[("mobile", gap.step_name)] * mobile_order_value
        )
        rows.append(
            {
                "step_name": gap.step_name,
                "worst_mobile_deficit": worst_deficit,
                "mobile_sessions_entered": gap.mobile_sessions_entered,
                "extra_sessions_reaching_step": extra_sessions,
                "purchase_rate_after_step": purchase_rate[("mobile", gap.step_name)],
                "mobile_order_value_usd": mobile_order_value,
                "extra_revenue_usd": extra_revenue,
            }
        )
    return pd.DataFrame(rows).sort_values("extra_revenue_usd", ascending=False, ignore_index=True)


def payment_step_test(
    step_conversion: pd.DataFrame,
    step_purchase: pd.DataFrame,
    order_value: pd.DataFrame,
    export_days: int,
    test_weeks: tuple[int, ...] = (4, 8, 12),
) -> pd.DataFrame:
    """Value of lifting payment-step conversion on every device, and what a test can detect.

    Assumptions: traffic during a test matches the sample's daily average; a 50/50 split; extra
    sessions that add payment info buy at the rate such sessions already do, at their device's
    average order value.
    """
    purchase_rate = purchase_rate_by_step(step_purchase)
    device_order_value = order_value_by_device(order_value)
    payment = step_conversion[step_conversion["step_name"] == PAYMENT_STEP]
    entered = int(payment["sessions_entered"].sum())
    baseline = payment["sessions_reached"].sum() / entered
    revenue_per_point = sum(
        row.sessions_entered
        * 0.01
        * purchase_rate[(row.device_category, PAYMENT_STEP)]
        * device_order_value[row.device_category]
        for row in payment.itertuples()
    )
    rows = []
    for weeks in test_weeks:
        per_arm = int(entered / export_days * 7 * weeks / 2)
        lift = detectable_rate(baseline, per_arm) - baseline
        rows.append(
            {
                "test_weeks": weeks,
                "sessions_per_arm": per_arm,
                "baseline_conversion": baseline,
                "detectable_lift_points": lift * 100,
                "revenue_per_point_usd": revenue_per_point,
                "revenue_at_detectable_lift_usd": revenue_per_point * lift * 100,
                "sessions_entering_in_sample": entered,
            }
        )
    return pd.DataFrame(rows)


def coupon_holdout_test(
    coupon_difference: pd.DataFrame, buyers_per_day: float, holdout_days: int = 90
) -> pd.DataFrame:
    """What a coupon holdout among first-time buyers can confirm, using 30-day repeat purchase.

    Assumptions: buyers arrive at the sample's daily rate, half of them in each arm. The first
    figure takes the observed difference as the true one; the second gives the smallest
    difference a holdout of holdout_days can detect.
    """
    row = coupon_difference[coupon_difference["window_days"] == 30].iloc[0]
    per_arm = sessions_per_arm(row["no_coupon_repeat_rate"], row["coupon_repeat_rate"])
    holdout_per_arm = int(buyers_per_day * holdout_days / 2)
    detectable = detectable_rate(row["no_coupon_repeat_rate"], holdout_per_arm)
    return pd.DataFrame(
        [
            {
                "window_days": 30,
                "no_coupon_repeat_rate": row["no_coupon_repeat_rate"],
                "coupon_repeat_rate": row["coupon_repeat_rate"],
                "buyers_per_arm_for_observed_difference": per_arm,
                "days_of_first_time_buyers_needed": 2 * per_arm / buyers_per_day,
                "holdout_days": holdout_days,
                "holdout_buyers_per_arm": holdout_per_arm,
                "holdout_detectable_difference_points": (detectable - row["no_coupon_repeat_rate"])
                * 100,
            }
        ]
    )
