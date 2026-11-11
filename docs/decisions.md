# Decisions

Newest at the bottom. Each entry: context, options, decision, consequences, and what would make me
revisit it.

## 2026-11-11 Publish SQL and aggregates only, because the dataset has no stated licence

- Context: Google's documentation for `ga4_obfuscated_sample_ecommerce` describes the dataset and
  invites exploration in the BigQuery sandbox, but states no licence for the data itself.
- Options: (a) use it and commit raw extracts; (b) use it and commit only SQL plus aggregated
  counts and rates; (c) switch to a synthetic event generator.
- Decision: (b). The repo contains the queries and small aggregate files (step counts, rates,
  intervals), never event rows or user identifiers. The README attributes the source.
- Consequences: anyone reproducing the numbers needs a Google account and a BigQuery sandbox
  project. The report build itself needs no Google access.
- Revisit if: Google publishes terms that restrict derived aggregates, or the dataset is withdrawn.

## 2026-11-11 Drop the 90-day repeat-purchase window

- Context: the card asks for 30, 60, and 90-day repeat purchase. The data covers 92 days
  (2020-11-01 to 2021-01-31). A 90-day window only fits first purchases made on 1 or 2 November.
- Options: (a) report 90 days on a two-day cohort; (b) report 90 days with survival-analysis
  extrapolation; (c) report 30 and 60 days only, each on the cohorts that can be followed for the
  full window.
- Decision: (c). The 30-day rate uses first purchases up to 2021-01-01; the 60-day rate uses first
  purchases up to 2020-12-02. Exact cut-offs are confirmed in milestone 1.
- Consequences: the 60-day rate rests on November buyers only, which includes the Black Friday
  period; the memo must say so.
- Revisit if: a longer export of the same store becomes public.

## 2026-11-11 Add a sample-size estimate to the "how to test it" part of each recommendation

- Context: current analyst postings ask for funnel and cohort SQL, BigQuery, Python for statistics,
  and experimentation: a Staff Product Analyst listing on Built In NYC (funnels, retention, cohorts,
  experimentation), a Data Analyst listing at Puffy (funnel leak analysis, BigQuery, Python
  statistics, experimentation), a Sales Data Analyst listing at DermaDream (cohort retention,
  BigQuery), and a Product Analyst listing at Kredivo in Jakarta (SQL required). The card already
  covers funnels, cohorts, and BigQuery.
- Options: (a) keep "how to test it" as prose; (b) add a minimum detectable effect and the sessions
  needed per arm for the first recommendation's A/B test.
- Decision: (b). It is one calculation on numbers the funnel already produces, and it turns "test
  it" into a plan the team can schedule.
- Consequences: one more function with tests in the statistics module.
- Revisit if: the memo grows past two pages because of it.

## 2026-11-11 Test the funnel and cohort logic in DuckDB on small fixtures

- Context: BigQuery cannot run in CI without a service-account key, and the sandbox has no free
  local emulator. The card asks for tests on small fixtures.
- Options: (a) tests that call BigQuery, run only on a laptop; (b) translate BigQuery SQL with a
  transpiler for tests; (c) split the SQL into two layers: a BigQuery-only flattening query (UNNEST
  of `event_params` and `items`) that writes one row per session step, and the funnel and cohort
  queries written in the subset of SQL that BigQuery and DuckDB share, run in BigQuery for real
  numbers and in DuckDB against fixtures in tests.
- Decision: (c). The same SQL text runs in both engines, so the tests check the queries that
  produce the published numbers. DuckDB is a widely used embedded engine that installs with pip.
- Consequences: the shared layer avoids engine-specific functions (for example `COUNTIF`,
  `DATE_DIFF`); dates are passed as integer day numbers. The flattening query is checked by
  reconciliation counts against the raw tables instead of fixtures.
- Revisit if: the shared subset forces a query that is hard to read.

## 2026-11-11 Build the report from committed aggregate files

- Context: Evidence can query BigQuery directly, but GitHub Pages builds in CI, which would then
  need Google credentials.
- Options: (a) Evidence BigQuery source with a key stored as a CI secret; (b) a pipeline command
  that writes small CSV files into `report/sources/`, which Evidence reads.
- Decision: (b). No credential leaves the laptop, and the published numbers are visible in the
  repo history.
- Consequences: the CSV files must be regenerated and committed when a query changes; CI checks
  that the report builds from them.
- Revisit if: the report needs data that is too large to commit.
