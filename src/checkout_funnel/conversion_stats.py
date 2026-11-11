"""Intervals and test sizing for checkout step conversion.

Wilson intervals keep their coverage near 95% for small counts and rates near 0 or 1, where the
textbook normal (Wald) interval undercovers; late checkout steps on tablets have small counts.
The mobile minus desktop gap uses Newcombe's hybrid score interval, built from two Wilson
intervals, for the same reason.
"""

import math
from dataclasses import dataclass

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (
    confint_proportions_2indep,
    proportion_confint,
    proportion_effectsize,
)


@dataclass(frozen=True)
class RateInterval:
    rate: float
    low: float
    high: float


def _check_counts(reached: int, entered: int, label: str) -> None:
    if entered <= 0:
        raise ValueError(f"{label}: no sessions entered the step, so its conversion is undefined.")
    if not 0 <= reached <= entered:
        raise ValueError(
            f"{label}: {reached} sessions reached the next step out of {entered} that entered; "
            "reached must be between 0 and entered. Check the funnel ordering rule."
        )


def step_conversion(reached: int, entered: int, confidence: float = 0.95) -> RateInterval:
    """Share of sessions that entered a step and reached the next one, with a Wilson interval."""
    _check_counts(reached, entered, "step conversion")
    low, high = proportion_confint(reached, entered, alpha=1 - confidence, method="wilson")
    return RateInterval(reached / entered, float(low), float(high))


def conversion_gap(
    mobile_reached: int,
    mobile_entered: int,
    desktop_reached: int,
    desktop_entered: int,
    confidence: float = 0.95,
) -> RateInterval:
    """Mobile minus desktop step conversion, with Newcombe's hybrid score interval."""
    _check_counts(mobile_reached, mobile_entered, "mobile")
    _check_counts(desktop_reached, desktop_entered, "desktop")
    low, high = confint_proportions_2indep(
        mobile_reached,
        mobile_entered,
        desktop_reached,
        desktop_entered,
        method="newcomb",
        compare="diff",
        alpha=1 - confidence,
    )
    gap = mobile_reached / mobile_entered - desktop_reached / desktop_entered
    return RateInterval(gap, float(low), float(high))


def sessions_per_arm(
    baseline_rate: float, target_rate: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Sessions each arm of a two-sided A/B test needs to detect a move from baseline to target."""
    for name, rate in (("baseline_rate", baseline_rate), ("target_rate", target_rate)):
        if not 0 < rate < 1:
            raise ValueError(f"{name} must be strictly between 0 and 1, got {rate}.")
    if baseline_rate == target_rate:
        raise ValueError(
            "baseline_rate and target_rate are equal, so there is no effect to detect."
        )
    effect = abs(proportion_effectsize(target_rate, baseline_rate))
    sessions = NormalIndPower().solve_power(
        effect_size=effect, alpha=alpha, power=power, ratio=1.0, alternative="two-sided"
    )
    return math.ceil(sessions)
