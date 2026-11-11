# Design review

Screenshot review of the Quarto report against docs/design-brief.md and the portfolio design
rules (anti-patterns, completeness, charts). Screenshots were captured with
`scripts/review_screenshots.py` at 375, 768, and 1440 px for all six pages, plus the error state;
review rounds are git-ignored, final screenshots are in docs/screenshots/.

## Round 1 (2026-11-11)

Failed:
- axe: `aria-prohibited-attr` on every chart (3 to 6 nodes per page). Observable Plot labels its
  mark groups with `aria-label` on elements that have no role.
- Sideways page scroll on the memo at 375 px: long file names in its source table.
- Funnel page lede printed "is points": an inline expression contained quotes, which Pandoc
  turned into typographic quotes and broke the JavaScript.
- Error state: with the CSV files blocked, the funnel page showed eleven red "OJS Runtime Error"
  boxes and broken sentences.
- Revenue chart at 375 px: the highlighted label ran off the right edge.
- Tables: captions were centred and scrolled out of view with a wide table on a phone; repeated
  "Interval" headers did not say which device they belonged to.
- Navbar wrapped onto two lines at 800 px; the site title was cut at 375 px; a search box with
  nothing worth searching.

Passed: memo-first layout, one bold element, finding-as-title on every chart, no KPI cards, no
pie or donut, bars start at zero, sentence-case labels, legend plus direct labels on the step
ladder, colour never the only signal (every mark has a text label and a table row).

## Round 2

Changes: charts became a single `role="img"` with Plot's group labels removed (numbers are in the
tables); `overflow-wrap` for code in tables; inline expressions without quotes; a loader that never
throws, one alert at the top of the page, dashes instead of `NaN`, and an empty-state box in place
of each chart; captions outside the scroll region; device-specific headers; navbar collapses below
992 px; shorter site title; search off.

Result: axe 0 violations and no sideways scroll on all 18 page and width combinations.

Failed: chart labels still wrapped late, because the wrap width was computed in characters while
Plot expects ems; the alert printed backticks around the rebuild command; captions were still
centred; nothing told a phone reader that a table scrolls sideways.

## Round 3

Changes: wrap width in ems; short labels on phones for the revenue chart; `<code>` in the alert;
left-aligned captions; a "Scroll sideways for more columns" hint that appears only when a table
is wider than the screen; halos behind chart labels where a reference line crosses them.

Result: axe 0 violations and no sideways scroll at 375, 768, and 1440 px; labels on one line on
phones; the error state shows one message that names the missing files and the fix.

## Lighthouse

Lighthouse 13.6.0, default mobile emulation with throttling, against the built site served
locally by Python's `http.server`, which does not compress files.

| Page | Performance | Accessibility | Best practices | SEO | CLS | LCP |
| --- | --- | --- | --- | --- | --- | --- |
| index | 62 | 100 | 100 | 100 | 0.018 | 6.2 s |
| memo | 63 | 100 | 100 | 100 | 0.008 | 6.1 s |
| funnel | 63 | 100 | 100 | 100 | 0.015 | 6.1 s |
| repeat-purchase | 51 | 100 | 100 | 100 | 0.223 | 6.2 s |
| revenue | 51 | 100 | 100 | 100 | 0.226 | 6.2 s |
| method | 53 | 100 | 100 | 100 | 0.199 | 6.1 s |

SEO rose from 91 to 100 after adding a meta description to every page. Layout shift on the index
fell from 0.66 to 0.02 after reserving the height of each chart and table.

Not fixed:
- Largest contentful paint is about 6 s under throttling. Most of the weight is Quarto's own
  Observable runtime (890 KB uncompressed) and Bootstrap CSS (491 KB), both served uncompressed
  here; GitHub Pages compresses them. The scores will be re-measured on the deployed site.
- Three pages keep a layout shift of about 0.2: numbers inside paragraphs arrive after the CSV
  files load and re-wrap their lines. A placeholder width made it worse (0.44) and was removed.
  The real fix is to compute those numbers at build time with Quarto's Python engine, which adds
  Jupyter to the build; not done, because the shift happens once, within 0.4 s, before anyone
  reads the paragraph.

## States checked

- Full data: all pages, three widths.
- Error: CSV requests blocked; one alert, dashes, empty-state boxes.
- Loading: the report has no loading indicator. Data arrives in under 0.4 s locally, and the
  space for each chart and table is reserved, so a skeleton would only add motion.
- Empty and partial data: not applicable; the report reads fixed files that the pipeline writes
  in full. Tables and charts handle zero rows with the same message as the error state.
- Long text and large numbers: the longest labels ("Add shipping details", "Coupon at first
  purchase") and the largest counts (205,899) were checked at 375 px.

## Content update after the outside review (2026-11-11)

Not a design round: the memo's claims changed (see docs/decisions.md, "Revisions after an outside
review"). The revenue page's chart now compares the lift an 8-week test detects on all devices
and on mobile only; its reserved height was cut from 600 to 440 px to match. The overview's chart
title and lede now describe a null result as a range. All 18 page and width combinations were
captured again: axe 0 violations, no sideways scroll. Screenshots and the demo were re-recorded so
their numbers match the current result files.

## Lighthouse on the deployed site (2026-11-11)

Same settings, against https://jeevallucas.github.io/p01-checkout-funnel/, which GitHub Pages
serves compressed.

| Page | Performance | Accessibility | Best practices | SEO | CLS | LCP |
| --- | --- | --- | --- | --- | --- | --- |
| index | 96 | 100 | 100 | 100 | 0.008 | 2.2 s |
| memo | 98 | 100 | 100 | 100 | 0.008 | 2.0 s |
| funnel | 98 | 100 | 100 | 100 | 0.011 | 2.0 s |
| repeat-purchase | 97 | 100 | 100 | 100 | 0.008 | 2.0 s |
| revenue | 97 | 100 | 100 | 100 | 0 | 2.0 s |
| method | 98 | 100 | 100 | 100 | 0.009 | 2.0 s |

The layout shift of about 0.2 measured locally on three pages does not appear on the deployed
site, so the build-time rendering listed under "Not fixed" is no longer needed.
