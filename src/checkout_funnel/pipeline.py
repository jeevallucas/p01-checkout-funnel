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
from checkout_funnel.sizing import coupon_holdout_test, mobile_only_upper_bound, payment_step_test
from checkout_funnel.sql_files import SQL_DIR, shared_query

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "report" / "sources" / "results"


def read_result(name: str) -> pd.DataFrame:
    path = RESULTS_DIR / f"{name}.csv"
    if not path.exists():
        raise SystemExit(f"{path} is missing; run `uv run pipeline funnel cohorts` first.")
    return pd.read_csv(path)


def write_result(result: pd.DataFrame, name: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # LF line endings keep the committed files identical whichever OS ran the pipeline.
    result.to_csv(RESULTS_DIR / f"{name}.csv", index=False, lineterminator="\n")


def run_profile(client: bigquery.Client) -> None:
    for sql_path in sorted((SQL_DIR / "profile").glob("*.sql")):
        result = run_query(client, sql_path.read_text(encoding="utf-8"), sql_path.name)
        write_result(result, f"profile_{sql_path.stem}")


def build_bigquery_table(client: bigquery.Client, name: str) -> str:
    sql = (SQL_DIR / "bigquery" / f"{name}.sql").read_text(encoding="utf-8")
    return f"`{build_work_table(client, sql, name)}`"


def run_shared(client: bigquery.Client, name: str, **tables: str) -> pd.DataFrame:
    return run_query(client, shared_query(name, **tables), f"{name}.sql")


def run_funnel(client: bigquery.Client) -> None:
    session_step_event = build_bigquery_table(client, "session_step_event")
    step_sessions = run_shared(
        client, "funnel_step_sessions", session_step_event=session_step_event
    )
    write_result(step_sessions, "funnel_step_sessions")
    write_result(step_conversion_table(step_sessions), "funnel_step_conversion")
    write_result(mobile_gap_table(step_sessions), "funnel_mobile_gap")
    for name in ("checkout_order_check", "step_purchase_rate"):
        write_result(
            run_shared(client, name, session_step_event=session_step_event), f"funnel_{name}"
        )


def run_cohorts(client: bigquery.Client) -> None:
    purchase_event = build_bigquery_table(client, "purchase_event")
    cohorts = run_shared(
        client,
        "repeat_purchase_cohorts",
        purchase_event=purchase_event,
        buyer=build_bigquery_table(client, "buyer"),
        export_first_day=str(day_number(EXPORT_FIRST_DAY)),
        export_last_day=str(day_number(EXPORT_LAST_DAY)),
    )
    write_result(repeat_rate_table(cohorts), "cohort_repeat_purchase")
    write_result(coupon_difference_table(cohorts), "cohort_coupon_difference")
    write_result(
        run_shared(client, "order_value", purchase_event=purchase_event), "cohort_order_value"
    )


def run_sizing() -> None:
    """Needs no BigQuery: it reads the aggregate files the funnel and cohorts steps wrote."""
    export_days = (EXPORT_LAST_DAY - EXPORT_FIRST_DAY).days + 1
    step_purchase = read_result("funnel_step_purchase_rate")
    order_value = read_result("cohort_order_value")
    write_result(
        mobile_only_upper_bound(read_result("funnel_mobile_gap"), step_purchase, order_value),
        "sizing_mobile_only",
    )
    write_result(
        payment_step_test(
            read_result("funnel_step_conversion"), step_purchase, order_value, export_days
        ),
        "sizing_payment_step",
    )
    cohorts = read_result("cohort_repeat_purchase")
    eligible_30 = cohorts[(cohorts["split"] == "all") & (cohorts["window_days"] == 30)]
    # Buyers whose first purchase leaves 30 days of follow-up arrive over export_days - 30 days.
    buyers_per_day = eligible_30["first_time_buyers"].iloc[0] / (export_days - 30)
    write_result(
        coupon_holdout_test(read_result("cohort_coupon_difference"), buyers_per_day),
        "sizing_coupon_holdout",
    )


BIGQUERY_STEPS = {"profile": run_profile, "funnel": run_funnel, "cohorts": run_cohorts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "steps",
        nargs="+",
        choices=[*BIGQUERY_STEPS, "sizing", "all"],
        help="profile, funnel, and cohorts query BigQuery; sizing works offline from their files",
    )
    args = parser.parse_args()
    steps = [*BIGQUERY_STEPS, "sizing"] if "all" in args.steps else args.steps
    bigquery_steps = [step for step in steps if step in BIGQUERY_STEPS]
    if bigquery_steps:
        client = bigquery_client()
        for step in bigquery_steps:
            BIGQUERY_STEPS[step](client)
    if "sizing" in steps:
        run_sizing()


if __name__ == "__main__":
    main()
