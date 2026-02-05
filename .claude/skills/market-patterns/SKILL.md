# Skill: Market Patterns

Understands the vintage guitar market dynamics that the scoring model relies on.

## Price vs Reverb range scoring curve

```
price <= reverb_lo          →  100  (best deal)
price == midpoint           →   75
price == reverb_hi          →   50  (fair)
price == 2 × reverb_hi     →    0  (avoid)
```

Linear interpolation between each breakpoint.  Missing price or Reverb data
returns a neutral 50.

## Collection-fit heuristics

| Condition | Delta |
|---|---|
| Brand not yet owned | +20 |
| Type < 25 % of collection | +15 |
| Exact brand + model already owned | -25 |

Base score is 50.  Clamped to [0, 100].

## Sold-detection grace period

A listing disappearing from the site does not immediately mean sold.
`searcher.py` records the first-miss timestamp in `.sold_candidates.json`
and only confirms the sale after 600 seconds (two full scrape cycles).
If the scrape itself returns zero results the check is skipped entirely.
