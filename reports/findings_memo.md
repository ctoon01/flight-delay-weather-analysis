# Findings Memo: Does Weather Cause Flight Delays?

## Bottom line

Yes — precipitation is associated with a statistically significant and
practically meaningful increase in departure delay, even after
controlling for carrier and origin airport. The effect is real, but it
explains only a small share of total delay variation — most delay is
driven by factors outside this dataset (air traffic congestion,
ground operations, downstream aircraft scheduling, etc.).

## What I tested

1. **Welch's two-sample t-test** comparing mean departure delay on
   hours with measurable precipitation vs. hours with none.
2. **Multiple linear regression** — `delay ~ precipitation + wind speed
   + visibility + carrier + origin` — to isolate weather's effect from
   carrier-specific and airport-specific baseline delay differences.

## What I found

| Metric | Clear hours | Precipitation hours |
|---|---|---|
| Flights | 305,907 | 21,086 |
| Mean departure delay | 11.4 min | 30.9 min |

- **Mean difference: 19.4 minutes** (95% CI: 18.6 to 20.2 min), t = 48.2, **p < 0.001**.
- In the regression, each additional inch of hourly precipitation is
  associated with an **85-minute increase** in average departure delay,
  holding carrier and origin constant (p < 0.001). Wind speed and
  visibility were also significant but smaller in magnitude (+0.4
  min/mph wind; −1.6 min per additional mile of visibility).
- **Model R² = 0.03.** This is disclosed deliberately, not buried:
  weather explains a real but small share of delay variance at the
  individual-flight level. The 95% CI and large sample size (n=326,848)
  make the effect statistically certain; they don't make weather the
  dominant cause of delay.

## Caveats

- This is 2013 data (NYC-origin flights only). Effect sizes are not
  assumed to generalize to other airports, eras, or aircraft mixes
  without re-validation.
- Precipitation is measured hourly at the origin airport only — it
  doesn't capture weather at the destination, en route, or at
  connecting hubs, all of which also drive real-world delay.
- The regression is observational, not causal in the strict sense:
  precipitation isn't randomly assigned. It's very likely a genuine
  causal contributor (the mechanism is physically obvious — fewer
  active runways, de-icing, reduced visibility approach procedures —
  and the effect is consistent and large), but I'm not claiming
  experimental-level causal proof from observational data.
- 8,255 flights (2.5%) were cancelled and excluded from the delay
  analysis, since cancelled flights have no delay value by definition.
  Cancellation rate itself is a separate, related question this memo
  doesn't address.

## Why this matters as a portfolio piece

This is the difference between a dashboard that shows numbers and an
analysis that answers a question with evidence, confidence intervals,
and stated limitations — which is what a data analyst is actually
asked to produce day to day.
