"""Command line entry point: `uv run pipeline <step>` writes aggregate CSVs for the report."""

import argparse
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

from checkout_funnel.bigquery_runner import bigquery_client, build_work_table, run_query
from checkout_funnel.cohorts import (
    EXPORT_FIRST_DAY,
    EXPORT_LAST_DAY,
    coupon_difference_table,
    day_number,
    repeat_rate_table,
)
from checkout_funnel.funnel import mobile_gap_table, step_conversion_table
from checkout_funnel.sql_files import SQL_DIR, shared_query

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "report" / "sources" / "results"


def write_result(result: pd.DataFrame, name: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # LF line endings keep the committed files identical whichever OS ran the pipeline.
    result.to_csv(RESULTS_DIR / f"{name}.csv", index=False, lineterminator="\n")


def run_profile(client: bigquery.Client) -> None:
    for sql_path in sorted((SQL_DIR / "profile").glob("*.sql")):
        result = run_query(client, sql_path.read_text(encoding="utf-8"), sql_path.name)
        write_result(result, f"profile_{sql_path.stem}")


def run_funnel(client: bigquery.Client) -> None:
    session_step_event = build_bigquery_table(client, "session_step_event")
    step_sessions = run_query(
        client,
        shared_query("funnel_step_sessions", session_step_event=session_step_event),
        "funnel_step_sessions.sql",
    )
    write_result(step_sessions, "funnel_step_sessions")
    order_check = run_query(
        client,
        shared_query("checkout_order_check", session_step_event=session_step_event),
        "checkout_order_check.sql",
    )
    write_result(order_check, "funnel_checkout_order_check")
    write_result(step_conversion_table(step_sessions), "funnel_step_conversion")
    write_result(mobile_gap_table(step_sessions), "funnel_mobile_gap")


def build_bigquery_table(client: bigquery.Client, name: str) -> str:
    sql = (SQL_DIR / "bigquery" / f"{name}.sql").read_text(encoding="utf-8")
    return f"`{build_work_table(client, sql, name)}`"


def run_cohorts(client: bigquery.Client) -> None:
    cohorts = run_query(
        client,
        shared_query(
            "repeat_purchase_cohorts",
            purchase_event=build_bigquery_table(client, "purchase_event"),
            buyer=build_bigquery_table(client, "buyer"),
            export_first_day=str(day_number(EXPORT_FIRST_DAY)),
            export_last_day=str(day_number(EXPORT_LAST_DAY)),
        ),
        "repeat_purchase_cohorts.sql",
    )
    write_result(repeat_rate_table(cohorts), "cohort_repeat_purchase")
    write_result(coupon_difference_table(cohorts), "cohort_coupon_difference")


STEPS = {"profile": run_profile, "funnel": run_funnel, "cohorts": run_cohorts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "steps", nargs="+", choices=[*STEPS, "all"], help="which sets of queries to run"
    )
    args = parser.parse_args()
    client = bigquery_client()
    for step in STEPS if "all" in args.steps else args.steps:
        STEPS[step](client)


if __name__ == "__main__":
    main()
