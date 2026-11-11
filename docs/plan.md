# Plan

Each milestone ends with a commit and a push. Done means the listed check passes.

## 1. Access and data profiling
- Python project with uv (pinned versions), ruff, pytest; a `pipeline` command that runs SQL files
  in BigQuery and writes aggregates.
- Profiling SQL: tables and date range, rows and events per day, sessions per device category,
  how often each funnel event appears, and the share of placeholder values (`<Other>`, `NULL`, `''`)
  in device, traffic source, coupon, transaction ID, and revenue fields.
- Output: `docs/data-profile.md` with the measured numbers and the rules for placeholders.
- Done when: the profile is written from query results and the repeat-purchase cut-off dates are
  confirmed.

## 2. Checkout funnel
- BigQuery flattening query: one row per session and funnel step, with device category and first
  timestamp.
- Shared-SQL funnel query: per step pair, sessions with the previous step that also have this
  step, by device (event order is unreliable in the sample; see docs/decisions.md).
- Python: Wilson 95% intervals for step conversion, Newcombe interval for the mobile minus desktop
  difference.
- Fixture tests in DuckDB: order ignored, repeated events, purchases without add_to_cart, devices.
- Done when: tests pass and `report/sources/` holds the funnel aggregates.

## 3. Repeat-purchase cohorts
- First purchase per user in the window, acquisition medium and source, coupon use at the first
  purchase; repeat purchase within 30 and 60 days, only for cohorts with full follow-up.
- Fixture tests: censoring cut-off, same-day second orders, users with placeholder medium.
- Done when: tests pass and the cohort aggregates are written.

## 4. Revenue at stake and memo
- Size the most a mobile-only fix could be worth (half of the worst mobile deficit the interval
  allows) and the gain from lifting the weakest checkout step for every device, as ranges, with
  every assumption listed.
- Minimum detectable effect and sessions per arm for testing the first recommendation.
- `docs/memo.md`: two pages, exactly three recommendations, each with a number, its assumption, and
  how to test it.
- Done when: every memo number traces to a file in `report/sources/`.

## 5. Evidence report on GitHub Pages
- Pages: memo, checkout funnel, repeat purchase, revenue at stake, method and data.
- Theme from `docs/design-brief.md`; screenshot review loop at 375, 768, and 1440 px, logged in
  `docs/design-review.md`; Playwright demo recording.
- GitHub Actions: lint, tests, report build, Pages deploy.
- Done when: the review passes and the Pages build is green.

## 6. README, review, publish
- README per the portfolio-readme checklist; fresh-clone run in an empty folder.
- /code-review, hiring-manager audit by a fresh subagent, fixes.
- Secret and forbidden-terms scan on the full history, weekly link check, Dependabot, then public.
