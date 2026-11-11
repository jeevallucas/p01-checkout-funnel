"""Add intervals to step conversion and compare mobile with desktop."""

import pandas as pd

from checkout_funnel.conversion_stats import conversion_gap, step_conversion

FUNNEL_STEPS = [
    "session_start",
    "view_item",
    "add_to_cart",
    "begin_checkout",
    "add_shipping_info",
    "add_payment_info",
    "purchase",
]


def _check_steps(step_pairs: pd.DataFrame) -> None:
    unknown_steps = set(step_pairs["step_name"]) - set(FUNNEL_STEPS)
    if unknown_steps:
        raise ValueError(
            f"Unexpected funnel steps {sorted(unknown_steps)}; "
            "update FUNNEL_STEPS to match sql/shared/funnel_step_sessions.sql."
        )


def step_conversion_table(step_pairs: pd.DataFrame) -> pd.DataFrame:
    """Add a Wilson interval to each device's step conversion.

    A step that no session entered has no defined conversion, so its row is left out rather
    than shown as zero.
    """
    _check_steps(step_pairs)
    entered = step_pairs[step_pairs["sessions_entered"] > 0]
    intervals = [
        step_conversion(int(row.sessions_reached), int(row.sessions_entered))
        for row in entered.itertuples()
    ]
    return entered.assign(
        conversion=[interval.rate for interval in intervals],
        conversion_low=[interval.low for interval in intervals],
        conversion_high=[interval.high for interval in intervals],
    ).reset_index(drop=True)


def mobile_gap_table(step_pairs: pd.DataFrame) -> pd.DataFrame:
    """Mobile minus desktop conversion per step, with its interval and whether it excludes zero."""
    _check_steps(step_pairs)
    by_device = step_pairs.set_index(["device_category", "step_name"])
    rows = []
    for step_number, step_name in enumerate(FUNNEL_STEPS[1:], start=2):
        try:
            mobile = by_device.loc[("mobile", step_name)]
            desktop = by_device.loc[("desktop", step_name)]
        except KeyError:
            raise ValueError(
                f"Step {step_name!r} is missing for mobile or desktop; the gap needs both."
            ) from None
        gap = conversion_gap(
            int(mobile["sessions_reached"]),
            int(mobile["sessions_entered"]),
            int(desktop["sessions_reached"]),
            int(desktop["sessions_entered"]),
        )
        rows.append(
            {
                "step_number": step_number,
                "step_name": step_name,
                "previous_step": FUNNEL_STEPS[step_number - 2],
                "mobile_sessions_entered": int(mobile["sessions_entered"]),
                "desktop_sessions_entered": int(desktop["sessions_entered"]),
                "mobile_conversion": mobile["sessions_reached"] / mobile["sessions_entered"],
                "desktop_conversion": desktop["sessions_reached"] / desktop["sessions_entered"],
                "gap": gap.rate,
                "gap_low": gap.low,
                "gap_high": gap.high,
                "gap_excludes_zero": gap.high < 0 or gap.low > 0,
            }
        )
    return pd.DataFrame(rows)
