"""Run the repo's SQL in BigQuery and return its (small) results."""

import os

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# The sandbox allows 1 TB of query processing per month. This cap stops a mistaken query (for
# example an accidental cross join) from using it up in one run.
MAX_BYTES_BILLED = 20 * 10**9

# Intermediate tables live in the user's own project. The public dataset is in the US
# multi-region, and BigQuery only joins tables stored in the same location.
WORK_DATASET = "checkout_funnel"
WORK_LOCATION = "US"


def bigquery_client() -> bigquery.Client:
    load_dotenv()
    project_id = os.environ.get("GCP_PROJECT_ID", "")
    if not project_id or project_id == "your-project-id":
        raise SystemExit(
            "GCP_PROJECT_ID is not set. Copy .env.example to .env and set it to the ID of the "
            "Google Cloud project that runs the queries (a BigQuery sandbox project is enough)."
        )
    return bigquery.Client(project=project_id)


def run_query(client: bigquery.Client, sql: str, label: str) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES_BILLED)
    job = client.query(sql, job_config=job_config)
    # Results are a few hundred rows at most, so the REST download is enough; the BigQuery
    # Storage API client would only add a dependency.
    result = job.result().to_dataframe(create_bqstorage_client=False)
    _report(label, job, f"{len(result)} rows")
    return result


def build_work_table(client: bigquery.Client, sql: str, table_name: str) -> str:
    """Write a query's result to the work dataset and return the table's full ID."""
    dataset = bigquery.Dataset(f"{client.project}.{WORK_DATASET}")
    dataset.location = WORK_LOCATION
    dataset = client.create_dataset(dataset, exists_ok=True)
    if dataset.location != WORK_LOCATION:
        raise SystemExit(
            f"Dataset {dataset.dataset_id} exists in {dataset.location}, but the GA4 sample is in "
            f"{WORK_LOCATION}. Delete that dataset or use another Google Cloud project."
        )
    table_id = f"{client.project}.{WORK_DATASET}.{table_name}"
    job_config = bigquery.QueryJobConfig(
        destination=table_id,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        maximum_bytes_billed=MAX_BYTES_BILLED,
    )
    job = client.query(sql, job_config=job_config)
    job.result()
    _report(table_name, job, f"table {table_id}")
    return table_id


def _report(label: str, job: bigquery.QueryJob, outcome: str) -> None:
    gigabytes = (job.total_bytes_processed or 0) / 10**9
    print(f"{label}: {outcome}, {gigabytes:.2f} GB processed")
