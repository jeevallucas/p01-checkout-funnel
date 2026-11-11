# Checkout and repeat purchase: what to fund next quarter

For the growth lead. Based on the Google Merchandise Store GA4 sample, 1 November 2020 to
31 January 2021 (92 days, 360,129 sessions, 5,357 orders). Revenue figures are the sample's US
dollars over those 92 days.

## The answer

Mobile shoppers do not drop out of checkout more than desktop shoppers. At every step the
difference is within noise, so a mobile-only checkout project has little to win. The step that
loses the most shoppers on every device is the move from shipping details to payment details:
38.7% of sessions that enter shipping never add payment.

First-time buyers who used a coupon come back at least as often as those who did not. Repeat
purchase is low for everyone: 5.9% within 30 days. Promotions should be judged on the first
order's margin, which this data does not contain, not on loyalty.

## Recommendation 1: fund a payment-step fix for all devices, not a mobile-only fix

- Number: each extra percentage point of shipping-to-payment conversion is worth about $5,000
  per 92 days (1.5% of revenue). The most a mobile-only fix could add, at any step, is $1,200
  (0.35% of revenue).
- Assumption: sessions that newly reach payment buy at today's rate (71.1%) and today's order
  value per device. The $1,200 ceiling assumes mobile is as far behind as the 95% interval
  allows and a fix closes half of that gap; the observed gap points the other way (mobile +1.3
  points at payment, interval -0.6 to +3.1).
- How to test: a 50/50 A/B test on all devices for 8 weeks gives 3,379 sessions per arm. It
  detects a lift of 3.3 points or more (61.3% to 64.6%), worth at least $16,500 per 92 days.
  Ship only if the lift's interval excludes zero; a smaller true lift will read as "no
  difference", so pick a change bold enough to move the step by 3 points.

## Recommendation 2: keep coupon-led acquisition, and decide on margin

- Number: within 30 days, 6.4% of coupon first-time buyers bought again, against 5.3% of the
  rest. The difference is +1.1 points, with an interval of -0.7 to +2.9. The data rules out
  coupon buyers repeating more than 0.7 points less often.
- Assumption: the `coupon` field on the first order marks a code the shopper entered. The
  window covers Black Friday and the holidays, when coupon use and gifting both peak; the
  60-day comparison rests on November buyers only (+1.5 points, -1.6 to +4.9).
- How to test: confirming a 1.1-point difference would need 6,884 buyers per arm, about 327
  days of first-time buyers. A 90-day holdout (no coupon for half of new visitors) detects only
  differences of 2.2 points or more. Run it only to guard against a large loss of repeat buyers,
  and spend the analysis effort on coupon cost per first order instead.

## Recommendation 3: repair two tracking problems before the next funnel review

- Number: in 61.8% of checkout sessions, shipping details are logged before checkout begins.
  70.5% of buyers carry more than one acquisition medium, although GA4 defines it as the first
  touch, which cannot change.
- Assumption: these come from tagging or the export, not from shoppers. Until they are fixed,
  funnel order and channel splits cannot be trusted; this memo works around them by ignoring
  event order and by reading the medium from each buyer's earliest event.
- How to test: run 20 scripted checkouts on each device with GA4 DebugView open and compare the
  logged order with the clicked order. Check that each test user keeps one medium across days.
  Done when the order matches in all 40 runs.

## What this analysis does not show

- Why shoppers stop at payment. Session replays or a short exit survey on that step should
  shape the change being tested.
- Channel effects on repeat purchase. Paid search buyers repeat at 7.1% within 30 days, but on
  156 buyers the interval runs from 4.0% to 12.2%, and the medium field is unreliable.
- Absolute revenue for the real store. The sample is obfuscated; the ratios are the transferable
  part.
- Sessions from the same shopper are treated as independent, which makes intervals slightly
  narrower than they should be.

## Where each number comes from

All files are in `report/sources/results/`; `uv run pipeline all` regenerates them.

| Number | File |
| --- | --- |
| Step conversion, 38.7% stop at payment, mobile gaps | `funnel_step_conversion.csv`, `funnel_mobile_gap.csv` |
| $5,000 per point, 8-week test size and lift | `sizing_payment_step.csv` |
| $1,200 mobile ceiling | `sizing_mobile_only.csv` |
| Orders, revenue, purchase rate after payment | `cohort_order_value.csv`, `funnel_step_purchase_rate.csv` |
| Repeat rates and coupon difference | `cohort_repeat_purchase.csv`, `cohort_coupon_difference.csv` |
| Holdout sizes | `sizing_coupon_holdout.csv` |
| Event order and medium stability | `funnel_checkout_order_check.csv`, `profile_user_acquisition_consistency.csv` |
