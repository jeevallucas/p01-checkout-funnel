"""Command line entry point: `uv run pipeline <step>` writes aggregate CSVs for the report."""

import argparse
from pathlib import Path

from checkout_funnel.bigquery_runner import bigquery_client, run_sql_file

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = REPO_ROOT / "sql"
RESULTS_DIR = REPO_ROOT / "report" / "sources" / "results"


def run_profile() -> None:
    client = bigquery_client()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for sql_path in sorted((SQL_DIR / "profile").glob("*.sql")):
        result = run_sql_file(client, sql_path)
        result.to_csv(RESULTS_DIR / f"profile_{sql_path.stem}.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["profile"], help="which set of queries to run")
    args = parser.parse_args()
    if args.step == "profile":
        run_profile()


if __name__ == "__main__":
    main()
