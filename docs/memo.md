# Checkout and repeat purchase: what to fund next quarter

For the growth lead. Based on the Google Merchandise Store GA4 sample, 1 November 2020 to
31 January 2021 (92 days, 360,129 sessions, 5,357 orders). Revenue figures are the sample's US
dollars over those 92 days.

## The answer

No checkout step shows a clear difference between mobile and desktop shoppers. The intervals
leave room for mobile to be up to 1.2 points worse or 3.2 points better at a step, so a
mobile-specific project starts without evidence of a mobile problem. Inside checkout, the largest
loss is before payment: 38.7% of sessions that add shipping details, which is nearly every session
that starts checkout, never add payment details. The rate is the same on mobile and desktop.

First-time buyers who used a coupon came back no less often than those who did not. Repeat
purchase is low for everyone: 5.9% within 30 days. Whether promotions pay depends on the first
order's margin, which this data does not contain.

## Recommendation 1: fund a payment-step change for every device

- Number: each extra point of shipping-to-payment conversion is worth about $5,000 per 92 days on
  all devices, against about $2,000 if only mobile gets the change. An 8-week test on all devices
  detects a lift of 3.3 points or more; the same test on mobile alone needs 5.1 points.
- Assumption: sessions that newly reach payment buy at today's rate (71.1%) and order value per
  device, and traffic matches the sample's 92-day average. That average includes the holiday
  peak. At January's pace, 63% of the average, the all-device test detects 4.1 points.
- How to test: a 50/50 test on all devices for 8 weeks, randomised by browser rather than session,
  because carts carry across visits. Ship only if the lift's interval excludes zero. A smaller true
  lift will read as "no difference", so choose a change bold enough to move the step by 3 to 4
  points.

Cart to checkout loses more sessions (60.8% of sessions with an add-to-cart do not begin checkout
in that visit). But 41.3% of purchasing sessions never add to cart in that visit, so carts carry
across visits and the session-level rate overstates the loss. It needs a browser-level analysis
before it competes for this quarter's slot.

## Recommendation 2: do not cut coupons on loyalty grounds; decide on margin

- Number: within 30 days, 6.4% of first-time buyers who used a coupon bought again, against 5.3%
  of the rest: +1.1 points, interval -0.7 to +2.9. A coupon penalty larger than 0.7 points is
  unlikely.
- Assumption: the `coupon` field marks a code at the first purchase. Three obfuscated codes cover
  54% of purchases, so they may be site-wide promotions rather than acquisition offers. The
  comparison is observational and spans Black Friday and the holidays; the 60-day comparison rests
  on November buyers only (+1.5 points, -1.6 to +4.9).
- How to test: confirming a 1.1-point difference would need 6,884 buyers per arm, about 327 days of
  first-time buyers at the sample's holiday-season pace. A 90-day holdout detects only differences
  of 2.2 points or more, and less once dilution is counted, because only the buyers who would use
  a code are affected. Measure coupon cost per first order instead.

## Recommendation 3: check two tracking problems before the next funnel review

- Number: in 61.8% of checkout sessions, shipping details are logged before checkout begins.
  70.5% of buyers carry more than one acquisition medium, although GA4 defines it as the first
  touch, which cannot change.
- Assumption: in this public sample, both may come from Google's obfuscation rather than from the
  store's tagging. The analysis works around them by ignoring event order and by reading the
  medium from each buyer's earliest event. If the store's own export shows them too, funnel order
  and channel splits cannot be trusted.
- How to test: run 20 scripted checkouts on each device with GA4 DebugView open and compare the
  logged order with the clicked order. Check that each test user keeps one medium across days.

## What this analysis does not show

- Why shoppers stop before payment. Shipping costs appear at this point and the payment form
  follows; session replays or a short exit survey should shape the change being tested.
- Channel effects on repeat purchase. Paid search buyers repeat at 7.1% within 30 days, but on 156
  buyers the interval runs from 4.0% to 12.2%, and the medium field is unreliable.
- People rather than browsers. GA4's user ID identifies a browser, so a shopper who switches
  devices counts as two users, and sessions from one shopper are treated as independent.
- Absolute revenue for the real store. The sample is obfuscated, and 366 first purchases (8.3%)
  record zero revenue; the ratios are the transferable part.

## Where each number comes from

All files are in `report/sources/results/`; `uv run pipeline all` regenerates them.

| Number | File |
| --- | --- |
| Step conversion, 38.7% stop before payment, mobile gaps | `funnel_step_conversion.csv`, `funnel_mobile_gap.csv` |
| Value per point, test sizes, January pace | `sizing_payment_step.csv` |
| Orders, purchase rate after payment | `cohort_order_value.csv`, `funnel_step_purchase_rate.csv` |
| Repeat rates and coupon difference | `cohort_repeat_purchase.csv`, `cohort_coupon_difference.csv` |
| Holdout sizes | `sizing_coupon_holdout.csv` |
| Event order and medium stability | `funnel_checkout_order_check.csv`, `profile_user_acquisition_consistency.csv` |
| Zero-revenue first purchases | `profile_purchase_quality.csv` |
