import pandas as pd
import pytest

from checkout_funnel.funnel import FUNNEL_STEPS, mobile_gap_table, step_conversion_table


def step_pairs(entered_reached_by_device):
    """Build the funnel_step_sessions result from {device: [(entered, reached), ...]}."""
    return pd.DataFrame(
        [
            {
                "device_category": device,
                "step_number": number,
                "step_name": FUNNEL_STEPS[number - 1],
                "previous_step": FUNNEL_STEPS[number - 2],
                "sessions_entered": entered,
                "sessions_reached": reached,
            }
            for device, pairs in entered_reached_by_device.items()
            for number, (entered, reached) in enumerate(pairs, start=2)
        ]
    )


SIX_STEPS = [(1000, 400), (400, 100), (100, 50), (50, 50), (50, 30), (30, 20)]


def test_each_step_gets_its_rate_and_a_wilson_interval():
    table = step_conversion_table(step_pairs({"mobile": SIX_STEPS}))
    add_to_cart = table[table["step_name"] == "add_to_cart"].iloc[0]
    assert add_to_cart["conversion"] == pytest.approx(0.25)
    assert add_to_cart["conversion_low"] < 0.25 < add_to_cart["conversion_high"]
    assert len(table) == len(FUNNEL_STEPS) - 1


def test_a_step_no_session_entered_is_left_out_instead_of_shown_as_zero():
    pairs = [(50, 20), (20, 5), (5, 0), (0, 0), (0, 0), (0, 0)]
    table = step_conversion_table(step_pairs({"tablet": pairs}))
    assert table["step_name"].tolist() == ["view_item", "add_to_cart", "begin_checkout"]
    assert table.iloc[-1]["conversion"] == 0.0


def test_gap_is_mobile_minus_desktop_and_flags_clear_differences():
    mobile = [(10000, 4000), (4000, 1000), (1000, 600), (600, 600), (600, 300), (300, 200)]
    desktop = [(10000, 4000), (4000, 1000), (1000, 600), (600, 600), (600, 450), (450, 300)]
    table = mobile_gap_table(step_pairs({"mobile": mobile, "desktop": desktop}))
    payment = table[table["step_name"] == "add_payment_info"].iloc[0]
    assert payment["gap"] == pytest.approx(0.5 - 0.75)
    assert payment["gap_excludes_zero"]
    view_item = table[table["step_name"] == "view_item"].iloc[0]
    assert view_item["gap"] == pytest.approx(0.0)
    assert not view_item["gap_excludes_zero"]


def test_gap_needs_both_devices():
    with pytest.raises(ValueError, match="missing for mobile or desktop"):
        mobile_gap_table(step_pairs({"mobile": SIX_STEPS}))


def test_an_unknown_step_name_is_reported_instead_of_ignored():
    rows = step_pairs({"mobile": SIX_STEPS})
    rows.loc[1, "step_name"] = "view_cart"
    with pytest.raises(ValueError, match="view_cart"):
        step_conversion_table(rows)
