"""Run the repo's SQL files in BigQuery and return their (small) results."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# The sandbox allows 1 TB of query processing per month. This cap stops a mistaken query (for
# example an accidental cross join) from using it up in one run.
MAX_BYTES_BILLED = 20 * 10**9


def bigquery_client() -> bigquery.Client:
    load_dotenv()
    project_id = os.environ.get("GCP_PROJECT_ID", "")
    if not project_id or project_id == "your-project-id":
        raise SystemExit(
            "GCP_PROJECT_ID is not set. Copy .env.example to .env and set it to the ID of the "
            "Google Cloud project that runs the queries (a BigQuery sandbox project is enough)."
        )
    return bigquery.Client(project=project_id)


def run_sql_file(client: bigquery.Client, sql_path: Path) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_BILLED)
    job = client.query(sql_path.read_text(encoding="utf-8"), job_config=job_config)
    result = job.result().to_dataframe()
    gigabytes = (job.total_bytes_processed or 0) / 10**9
    print(f"{sql_path.name}: {len(result)} rows, {gigabytes:.2f} GB processed")
    return result
