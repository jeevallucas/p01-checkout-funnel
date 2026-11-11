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

## 2026-11-11 Count an ordered, session-based funnel

- Context: the growth lead asks where shoppers drop out of checkout. GA4 events can arrive out of
  order, repeat, or skip steps, and one user can have many sessions over three months.
- Options: (a) user-based funnel over the whole window; (b) session-based open funnel, where a
  session counts at a step if it has the event at all; (c) session-based ordered funnel, where a
  session counts at a step only if the event happens at or after it reached the previous step.
- Decision: (c). A checkout fix changes what happens inside one visit, so the session is the unit
  an A/B test would randomise and measure. Ordering stops a purchase without begin_checkout from
  inflating the later steps. Every event counts, not only each step's first, so a later repeat
  still satisfies the order; equal timestamps count as in order because GA4 batches events.
- Consequences: sessions without session_start are left out; the profile reports how many. A user
  with several sessions counts several times, so intervals treat sessions as independent, which
  slightly understates their width.
- Revisit if: the profile shows that many purchases happen in sessions that never reach
  begin_checkout, which would mean the event tagging, not the shopper, skips steps.

## 2026-11-11 Dependencies beyond the card's stack

- `db-dtypes` is required by the BigQuery client to turn query results into pandas frames.
- `python-dotenv` reads `GCP_PROJECT_ID` from `.env`, so no project ID is typed into commands.
- `duckdb` (dev only) runs the shared SQL against test fixtures; see the testing decision above.
- `sqlfluff` (dev only) lints SQL, as the workspace standard asks.

## 2026-11-11 Cohort definitions, set by the data profile

- Context: the profile (docs/data-profile.md) shows that `traffic_source.medium` changes across
  a user's events for 70.5% of buyers, that item-level coupons are always `(not set)`, and that
  20.6% of buyers were first seen before the window.
- Options for the medium: (a) the medium on the first purchase event; (b) the medium on the
  user's earliest event in the window; (c) drop the medium split and keep coupon use only.
- Decision: (b), with placeholders as an "unknown" row, because the earliest event is the closest
  thing to a first touch that the sample offers. The memo states that this split is weaker than
  the coupon split. Coupon use comes from the `coupon` event parameter on the first purchase
  event. A first-time buyer is a user first seen on or after 2020-11-01. A repeat is a purchase on
  a later calendar day within 30 or 60 days.
- Consequences: the medium comparison carries a caveat in every place it appears. Same-day second
  orders are not counted, which makes repeat rates slightly conservative but immune to the 335
  purchase events that repeat a transaction ID.
- Revisit if: a version of the sample with a stable first-touch field appears, or the coupon
  parameter turns out to be set by something other than a shopper's code.

## 2026-11-11 Replace the ordered funnel with per-step pairs that ignore event order

- Context: the first funnel run used the ordered rule recorded above. Only 1,776 of the 4,848
  purchasing sessions passed it. `checkout_order_check.sql` shows why: in 6,862 of 11,106 checkout
  sessions (61.8%) the first `add_shipping_info` is timestamped before the first `begin_checkout`,
  and 2,000 of 4,848 purchasing sessions (41.3%) have no `add_to_cart`, because the cart was
  filled in an earlier visit. The ordered rule turned both into drop-off that did not happen.
- Options: (a) keep the ordered rule and report the artefact; (b) a closed funnel that requires
  every earlier step in any order; (c) measure each step pair on its own: of the sessions with the
  previous step's event, the share that also has this step's event, in any order.
- Decision: (c). It answers "where do sessions stop" without trusting the sample's timestamps,
  and a returning shopper who checks out without re-adding to cart still counts from
  begin_checkout onward. This supersedes the ordered-funnel entry above; the session as the unit
  stays.
- Consequences: step rates are conditional on the previous step only, so multiplying them does not
  give the session-to-purchase rate. `add_shipping_info` follows `begin_checkout` in 99.97% or more
  of sessions on every device, so it is not a separate place to fix. The SQL is shorter: one
  aggregation instead of seven chained joins.
- Revisit if: a sample with reliable timestamps is used, where order carries information.

## 2026-11-11 No mobile gap: reframe the first recommendation and the sizing

- Context: the card assumes some checkout step loses more mobile than desktop shoppers. The
  measured gaps (mobile minus desktop) all have 95% intervals that include zero. The most a mobile
  deficit can be at any step, by the interval's lower bound, is 1.2 points (purchase after
  payment); at payment after shipping it is 0.6 points.
- Options: (a) report the largest point estimate as "the worst mobile step"; (b) state that the
  data rules out a mobile-specific problem, and size two things instead: the most a mobile-only
  fix could be worth (half of the interval's worst case, as the card's sizing rule asks), and the
  gain from lifting the weakest checkout step for all devices.
- Decision: (b). Option (a) would present noise as a finding, which is the error the intervals
  exist to prevent. The first recommendation becomes "do not fund a mobile-only checkout fix; fund
  the shipping-to-payment step for every device", with its A/B test size.
- Consequences: milestone 4 sizes both scenarios. The memo explains why the absence of a gap is
  itself the decision-relevant result.
- Revisit if: a sample from after the store's checkout changes, or with more mobile sessions,
  shows an interval that excludes zero.

## 2026-11-11 Recommend an 8-week payment-step test

- Context: the memo's first recommendation needs a test the team can run inside one quarter.
  `sizing_payment_step.csv` gives the smallest lift each length can detect at the sample's
  traffic: 4 weeks 4.6 points, 8 weeks 3.3 points, 12 weeks 2.7 points.
- Options: 4, 8, or 12 weeks.
- Decision: 8 weeks. Four weeks only detects lifts larger than most checkout changes produce; 12
  weeks leaves no time in the quarter to ship the winner.
- Consequences: a true lift below 3.3 points will usually read as "no difference", so the memo
  asks for a change bold enough to move the step by that much.
- Revisit if: traffic during the test is clearly higher or lower than the sample's daily
  average.
