"""Intervals and test sizing for conversion and repeat-purchase rates.

Wilson intervals keep their coverage near 95% for small counts and rates near 0 or 1, where the
textbook normal (Wald) interval undercovers; tablet checkout steps and repeat purchases have small
counts. Differences between groups (mobile minus desktop, coupon minus no coupon) use Newcombe's
hybrid score interval, built from two Wilson intervals, for the same reason.
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


def _check_counts(successes: int, trials: int, label: str) -> None:
    if trials <= 0:
        raise ValueError(f"{label}: the group is empty, so its rate is undefined.")
    if not 0 <= successes <= trials:
        raise ValueError(
            f"{label}: {successes} successes out of {trials}; successes must be between 0 and "
            "the group size. Check the query that produced the counts."
        )


def rate_with_interval(successes: int, trials: int, confidence: float = 0.95) -> RateInterval:
    """A rate such as step conversion or repeat purchase, with a Wilson interval."""
    _check_counts(successes, trials, "rate")
    low, high = proportion_confint(successes, trials, alpha=1 - confidence, method="wilson")
    return RateInterval(successes / trials, float(low), float(high))


def rate_difference(
    successes_a: int,
    trials_a: int,
    successes_b: int,
    trials_b: int,
    confidence: float = 0.95,
) -> RateInterval:
    """Rate of group a minus rate of group b, with Newcombe's hybrid score interval."""
    _check_counts(successes_a, trials_a, "group a")
    _check_counts(successes_b, trials_b, "group b")
    low, high = confint_proportions_2indep(
        successes_a,
        trials_a,
        successes_b,
        trials_b,
        method="newcomb",
        compare="diff",
        alpha=1 - confidence,
    )
    difference = successes_a / trials_a - successes_b / trials_b
    return RateInterval(difference, float(low), float(high))


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
