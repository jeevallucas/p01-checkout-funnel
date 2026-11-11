import pytest
from statsmodels.stats.proportion import proportion_effectsize

from checkout_funnel.conversion_stats import (
    detectable_rate,
    rate_difference,
    rate_with_interval,
    sessions_per_arm,
)


def test_wilson_interval_matches_newcombe_1998_worked_example():
    # Newcombe (1998), Statistics in Medicine 17:857-872, example 81/263: Wilson 0.2553 to 0.3662.
    result = rate_with_interval(81, 263)
    assert result.rate == pytest.approx(81 / 263)
    assert result.low == pytest.approx(0.2553, abs=5e-5)
    assert result.high == pytest.approx(0.3662, abs=5e-5)


def test_wilson_interval_stays_inside_zero_and_one_at_the_edges():
    none_reached = rate_with_interval(0, 12)
    all_reached = rate_with_interval(12, 12)
    assert none_reached.low == pytest.approx(0.0, abs=1e-12) and none_reached.high > 0.0
    assert all_reached.high == pytest.approx(1.0) and all_reached.low < 1.0


def test_gap_interval_matches_newcombe_1998_hybrid_score_example():
    # Newcombe (1998), Statistics in Medicine 17:873-890, 56/70 minus 48/80, method 10:
    # difference 0.2000, interval 0.0524 to 0.3339.
    result = rate_difference(56, 70, 48, 80)
    assert result.rate == pytest.approx(0.2)
    assert result.low == pytest.approx(0.0524, abs=5e-5)
    assert result.high == pytest.approx(0.3339, abs=5e-5)


def test_difference_is_negative_when_the_first_group_converts_worse():
    result = rate_difference(30, 100, 50, 100)
    assert result.rate == pytest.approx(-0.2)
    assert result.low < result.rate < result.high < 0


@pytest.mark.parametrize(
    ("reached", "entered", "message"),
    [
        (0, 0, "the group is empty"),
        (5, 4, "successes must be between 0"),
        (-1, 4, "successes must be between 0"),
    ],
)
def test_invalid_counts_raise_an_actionable_error(reached, entered, message):
    with pytest.raises(ValueError, match=message):
        rate_with_interval(reached, entered)


def test_sessions_per_arm_matches_cohen_table_for_small_effect():
    # Cohen (1988), table 6.4.1: h = 0.20, two-sided alpha 0.05, power 0.80 needs 392 per group.
    baseline = 0.5
    target = next(
        p / 10000 for p in range(5000, 10000) if proportion_effectsize(p / 10000, baseline) >= 0.2
    )
    assert sessions_per_arm(baseline, target) in (392, 393)


def test_sessions_per_arm_grows_as_the_lift_shrinks():
    assert sessions_per_arm(0.30, 0.31) > sessions_per_arm(0.30, 0.33)


@pytest.mark.parametrize(("baseline", "target"), [(0.0, 0.1), (0.3, 1.0), (0.3, 0.3)])
def test_sessions_per_arm_rejects_rates_it_cannot_size(baseline, target):
    with pytest.raises(ValueError):
        sessions_per_arm(baseline, target)


def test_detectable_rate_round_trips_with_sessions_per_arm():
    target = detectable_rate(0.60, 1500)
    assert 0.60 < target < 0.70
    assert sessions_per_arm(0.60, target) in (1500, 1501)


def test_detectable_rate_shrinks_with_more_traffic():
    assert detectable_rate(0.60, 6000) < detectable_rate(0.60, 1500)
