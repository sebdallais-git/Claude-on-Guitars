# Command: /recommend

**What it does:** Scores all active listings against the current budget and
collection, then writes the top-N recommendations into the
`Recommendations` sheet of `outputs/listings.xlsx`.

**How to run:**
```bash
python3 scripts/scorer.py
```

Output includes a terminal table and the colour-coded Excel sheet.
Budget and weights are read from `data/budget.json`.
