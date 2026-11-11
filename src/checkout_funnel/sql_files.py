"""Locate the repo's SQL files and fill table names into the shared queries."""

from pathlib import Path

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def shared_query(name: str, **tables: str) -> str:
    """Read sql/shared/<name>.sql and substitute its table references, such as {session_step_event}.

    The same text runs in BigQuery (real data) and DuckDB (test fixtures), so only table names
    differ between the two.
    """
    template = (SQL_DIR / "shared" / f"{name}.sql").read_text(encoding="utf-8")
    try:
        return template.format(**tables)
    except KeyError as missing:
        raise ValueError(
            f"Shared query {name!r} needs a table name for {missing}; "
            "pass it as a keyword argument."
        ) from None
