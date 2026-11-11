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
| Context grey | #8C959F | Comparison segments (desktop, other mediums), gridlines are lighter | 3.0:1 (marks only) |
| Mobile blue | #0072B2 | Mobile sessions, the segment the checkout decision is about | 5.2:1 |
| Promotion green | #009E73 | Buyers acquired through a coupon or paid traffic; text variant #00704F | 3.4:1 marks, 6.1:1 text |
| Drop-off vermillion | #D55E00 | The loss being sized: the worst gap and its annotation; text variant #A84300 | 3.9:1 marks, 6.1:1 text |

Supporting neutrals: muted text #59636E (6.1:1), rules #D8DEE4, table header panel #F3F5F7.
Blue, green, and vermillion come from the Okabe-Ito colour-blind-safe set. Every coloured mark also
carries a direct text label, so colour is never the only signal.

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
|     |  [ gap ladder chart, 960 px ---------------------- ]|
|     |  Recommendation 2 ...........  number + interval   |
|     |  [ repeat-purchase bars ]                          |
|     |  Recommendation 3 ...........  number + range      |

375 px
| Memo title                |
| The answer                |
| Recommendation 1          |
| [ gap ladder, steps as    |
|   rows, labels inside ]   |
| ...                       |
```

Pages: Memo (home), Checkout funnel, Repeat purchase, Revenue at stake, Method and data.

## One bold element
The gap ladder on the memo page: one row per funnel step, mobile and desktop step conversion as two
dots with 95% interval whiskers, and the widest mobile shortfall drawn in vermillion with a direct
label in the form "<step>: mobile <n> points below desktop", filled from the measured values. Everything
else is quiet tables and plain charts in grey and blue.

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
  marks promotion-acquired buyers, so the same colour never means two segments.
- "Orange" became Okabe-Ito vermillion with a darker text variant, because the usual orange
  (#E69F00) fails contrast for labels (2.3:1).
- A dashboard grid was the obvious layout. Changed to a memo-first column, because the user's job
  is to make two decisions, not to monitor metrics.
- The default font in Evidence is Inter. Changed to IBM Plex Sans and its condensed width, because
  dense step labels must fit a phone and no other project here uses Plex.
