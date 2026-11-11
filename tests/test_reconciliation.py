from checkout_funnel.reconciliation import reconciliation_failures

MATCHING = {
    "raw_purchase_events": 5692,
    "table_purchase_events": 5692,
    "raw_buyers": 4419,
    "table_buyers": 4419,
    "raw_purchase_sessions": 4848,
    "table_purchase_sessions": 4848,
    "user_transaction_ids_on_two_days": 0,
}


def test_matching_counts_pass():
    assert reconciliation_failures(MATCHING) == []


def test_a_mismatch_names_the_count_and_both_values():
    failures = reconciliation_failures({**MATCHING, "table_buyers": 4310})
    assert failures == ["buyers: raw export has 4,419, work table has 4,310"]


def test_a_transaction_id_on_two_days_fails_the_repeat_rule():
    failures = reconciliation_failures({**MATCHING, "user_transaction_ids_on_two_days": 3})
    assert len(failures) == 1
    assert "count them as repeats" in failures[0]
