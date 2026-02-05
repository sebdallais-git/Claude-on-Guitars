# Command: /update-budget

**What it does:** Opens `data/budget.json` so you can adjust the total
budget, amount spent, scoring weights, or the number of recommendations.

**File:** `data/budget.json`

```json
{
    "total":      20000,
    "spent":      0,
    "weights": {
        "value":      0.40,
        "appreciate": 0.30,
        "fit":        0.30
    },
    "top_n": 10
}
```

After editing, run `/recommend` (`python3 scripts/scorer.py`) to refresh
the Recommendations sheet with the updated values.
