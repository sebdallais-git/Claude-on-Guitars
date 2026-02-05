# Skill: Collection Profile

Manages the user's owned-guitar collection and exposes it to the scoring
and valuation layers.

## Data format — data/collection.json

An array of guitar objects:

```json
[
  {
    "brand":         "Gibson",
    "model":         "Les Paul Standard",
    "type":          "Electric",
    "year":          "1959",
    "condition":     "Very Good+",
    "paid":          4500,
    "current_value": null,
    "value_1y":      null,
    "value_2y":      null,
    "notes":         "Original PAFs"
  }
]
```

`current_value`, `value_1y`, `value_2y` are populated by `valuation.py`
after a Reverb lookup.  `paid` and `notes` are user-entered.

## How the scorer uses it

`_score_fit()` in `scorer.py` reads the collection to check:
- Which brands are already owned (diversification bonus)
- Which brand+model combos are duplicates (penalty)
- Type distribution (under-represented type bonus)

An empty collection returns a neutral fit score of 50 for every listing.
