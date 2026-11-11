"""Compare raw-export counts with the work tables the BigQuery-only queries build."""

PAIRS = [
    ("purchase events", "raw_purchase_events", "table_purchase_events"),
    ("buyers", "raw_buyers", "table_buyers"),
    ("purchasing sessions", "raw_purchase_sessions", "table_purchase_sessions"),
]


def reconciliation_failures(counts: dict[str, int]) -> list[str]:
    """Messages for every count that does not match; an empty list means the tables agree."""
    failures = [
        f"{label}: raw export has {counts[raw]:,}, work table has {counts[table]:,}"
        for label, raw, table in PAIRS
        if counts[raw] != counts[table]
    ]
    if counts["user_transaction_ids_on_two_days"]:
        failures.append(
            f"{counts['user_transaction_ids_on_two_days']:,} transaction IDs appear on two days "
            "for the same user, so the repeat-purchase rule would count them as repeats; "
            "exclude them in sql/shared/repeat_purchase_cohorts.sql"
        )
    return failures
