"""Add intervals to repeat-purchase rates and compare coupon with no-coupon first-time buyers."""

from datetime import date

import pandas as pd

from checkout_funnel.conversion_stats import rate_difference, rate_with_interval

EXPORT_FIRST_DAY = date(2020, 11, 1)
EXPORT_LAST_DAY = date(2021, 1, 31)


def day_number(day: date) -> int:
    """Days since 1970-01-01, the integer day format the shared SQL uses (BigQuery UNIX_DATE)."""
    return (day - date(1970, 1, 1)).days


def repeat_rate_table(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Add a Wilson interval to each segment's repeat-purchase rate; empty segments are left out."""
    buyers = cohorts[cohorts["first_time_buyers"] > 0]
    intervals = [
        rate_with_interval(int(row.repeat_buyers), int(row.first_time_buyers))
        for row in buyers.itertuples()
    ]
    return buyers.assign(
        repeat_rate=[interval.rate for interval in intervals],
        repeat_rate_low=[interval.low for interval in intervals],
        repeat_rate_high=[interval.high for interval in intervals],
    ).reset_index(drop=True)


def coupon_difference_table(cohorts: pd.DataFrame) -> pd.DataFrame:
    """Coupon minus no-coupon repeat rate per follow-up window, with Newcombe's interval."""
    coupon_split = cohorts[cohorts["split"] == "coupon at first purchase"].set_index(
        ["window_days", "segment"]
    )
    rows = []
    for window_days in sorted(coupon_split.index.get_level_values("window_days").unique()):
        try:
            coupon = coupon_split.loc[(window_days, "coupon")]
            no_coupon = coupon_split.loc[(window_days, "no coupon")]
        except KeyError:
            raise ValueError(
                f"The {window_days}-day cohort lacks a coupon or a no-coupon segment; "
                "the comparison needs both."
            ) from None
        difference = rate_difference(
            int(coupon["repeat_buyers"]),
            int(coupon["first_time_buyers"]),
            int(no_coupon["repeat_buyers"]),
            int(no_coupon["first_time_buyers"]),
        )
        rows.append(
            {
                "window_days": int(window_days),
                "coupon_buyers": int(coupon["first_time_buyers"]),
                "no_coupon_buyers": int(no_coupon["first_time_buyers"]),
                "coupon_repeat_rate": coupon["repeat_buyers"] / coupon["first_time_buyers"],
                "no_coupon_repeat_rate": no_coupon["repeat_buyers"]
                / no_coupon["first_time_buyers"],
                "difference": difference.rate,
                "difference_low": difference.low,
                "difference_high": difference.high,
                "difference_excludes_zero": difference.high < 0 or difference.low > 0,
            }
        )
    return pd.DataFrame(rows)
