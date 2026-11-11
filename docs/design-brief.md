# Design brief

The report is a static Evidence site: a decision memo first, with the evidence pages behind it.

## Users and context
- The growth lead and two or three teammates, on laptops (1366-1440 px), in the office, reading for
  10-15 minutes before a quarterly planning meeting.
- During the meeting someone reopens one chart on a phone (375 px) to settle a question.
- They know funnels and conversion rates. They do not want to learn a tool to read the answer.

## Top 3 tasks, in their words
1. "Which checkout step loses the most mobile shoppers compared with desktop, and is that real or
   noise?"
2. "Do people we got with coupons or paid ads come back and buy again?"
3. "If we fix that step, roughly how much money is it worth, and what are we assuming?"

## Feel
Analytical, calm, dense. Rejected: salesy. No big hero numbers that shout without a comparison.

## References
- Amplitude funnel chart. Take: one bar group per step, conversion between steps printed at the
  step, a segment comparison side by side. Avoid: the purple product chrome and the control panel
  above every chart.
- GA4 Explorations funnel. Take: abandonment shown at the step where it happens. Avoid: numbers that
  appear only in tooltips; the phone reader cannot hover.
- Mixpanel insights with significance. Take: a comparison marked as significant or not, next to the
  number. Avoid: many coloured segments in one chart.

## Typography
- IBM Plex Sans for prose and headings. It has tabular figures, so numbers line up in tables, and
  its engineered shapes suit an analytics document. No other project in this workspace uses it.
- IBM Plex Sans Condensed for chart axes, direct labels, and table cells, so seven funnel steps and
  their labels fit a 375 px screen without wrapping.
- Type scale (ratio 1.25): 13 px axis labels and table cells, 16 px body, 20 px section lede, 25 px
  page headings, 31 px memo title. Body line height 1.5; prose measure at most 68 characters.
- Headings and labels in sentence case. Numbers use tabular figures and thousands separators.

## Palette
Every colour has one meaning across all pages.

| Name | Hex | Role | Contrast on white |
| --- | --- | --- | --- |
| Ink | #202124 | Text and axis lines | 16.1:1 |
| Paper | #FFFFFF | Page and chart background | - |
| Context grey | #9AA3AD | Comparison segments (desktop, buyers without a coupon, other mediums) | 2.5:1 (marks only) |
| Mobile blue | #0072B2 | Mobile sessions, the segment the card's question is about | 5.2:1 |
| Promotion green | #007A5E | Buyers who used a coupon at their first purchase | 5.3:1 |
| Drop-off vermillion | #D55E00 | The step to fund and its annotation; text variant #A84300 | 3.9:1 marks, 6.1:1 text |

Supporting neutrals: muted text #59636E (6.1:1), rules and gridlines #D8DEE4, table header panel
#F3F5F7.

Checked with the dataviz skill's palette validator (2026-11-11). Blue against grey: normal-vision
difference 21.2, colour-blind difference 17.7. Green against grey: 22.1 and 17.6. The validator
flags grey's low chroma and 2.5:1 contrast; both are intended, because grey means "context, not the
point". The relief the validator asks for is in place: every mark has a direct text label and every
chart has a table with the same numbers. The first draft used grey #8C959F and green #009E73, which
the validator failed against each other (normal-vision difference 13.7).

The report is light only. The growth lead reads it in an office, and one validated light palette
is better than an unvalidated dark one.

## Density
- The full funnel, seven steps by two devices with intervals, fits one laptop screen without
  scrolling.
- Tables carry the exact numbers; charts carry the comparison. The cohort table has at most eight
  rows.

## Layout
One left-aligned column. Prose stays at 68 characters; charts and tables may run wider (up to
960 px) but share the same left edge, so the eye never re-centres.

```
1440 px
| nav |  Memo title (31)                                   |
|     |  The answer in two sentences                       |
|     |  Recommendation 1 ...........  number + interval   |
|     |  [ step ladder chart, 960 px --------------------- ]|
|     |  Recommendation 2 ...........  number + interval   |
|     |  [ repeat-purchase bars ]                          |
|     |  Recommendation 3 ...........  number + range      |

375 px
| Memo title                |
| The answer                |
| Recommendation 1          |
| [ step ladder, steps as   |
|   rows, labels inside ]   |
| ...                       |
```

Pages: Memo (home), Checkout funnel, Repeat purchase, Revenue at stake, Method and data.

## One bold element
The step ladder on the memo page: one row per funnel step, mobile (blue) and desktop (grey) step
conversion as two dots with 95% interval whiskers. The dots sit on top of each other at every
step, which is the first finding: there is no mobile gap. The payment step's row carries a
vermillion band and a direct label, "38.7% of sessions stop here on every device", filled from the
measured values, which is the second finding. Everything else is quiet tables and plain charts in
grey, blue, and green.

The first version of this brief planned to highlight "the widest mobile shortfall". The data has
none (docs/decisions.md, 2026-11-11), so the highlight moved to the step worth funding.

Each mark has an SVG title, so hovering or focusing shows its value and interval; the same values
are in direct labels and tables, so nothing depends on hover.

## Avoid list for this project
- Evidence's default row of KPI cards (BigValue) above an area chart; numbers always appear with
  their comparison and interval.
- A funnel drawn as a tapering trapezoid; it hides the step rates that matter.
- Donut or pie charts for medium mix; use sorted horizontal bars.
- ALL-CAPS table headers or eyebrow labels; monospace data labels; metadata joined by middle dots.
- Gradient fills, shadows on charts, hover-only numbers.
- Evidence's default palette leaking into any chart.

## Review against the frontend-design process
The card's starting point was "neutral greys, one blue for the selected segment, orange for
drop-off". Reviewed against the brief:
- Neutral grey with one blue is the default for any analytics page. Kept, because the user compares
  one segment against the rest, but narrowed: blue now means mobile only, and a second hue (green)
  marks coupon buyers, so the same colour never means two segments.
- "Orange" became Okabe-Ito vermillion with a darker text variant, because the usual orange
  (#E69F00) fails contrast for labels (2.3:1).
- A dashboard grid was the obvious layout. Changed to a memo-first column, because the user's job
  is to make two decisions, not to monitor metrics.
- The default font in Evidence is Inter. Changed to IBM Plex Sans and its condensed width, because
  dense step labels must fit a phone and no other project here uses Plex.
