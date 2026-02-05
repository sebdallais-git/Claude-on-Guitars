# Advisor agent

**Role:** Owns `scripts/scorer.py` and `data/budget.json`.  Scores every
active listing on three dimensions (value, appreciation, collection fit),
ranks them, and writes the colour-coded Recommendations sheet into
`outputs/listings.xlsx`.

**Key responsibilities:**
- Three-dimension scoring (_score_value, _score_appreciation, _score_fit)
- Reading budget and weights from `data/budget.json`
- Writing / replacing the Recommendations Excel sheet
- Budget-aware greying of over-budget rows

**When to invoke this agent:**
- Scoring-weight or budget changes
- New scoring dimensions or rule changes
- Recommendations sheet formatting
