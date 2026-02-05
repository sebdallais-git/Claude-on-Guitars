# Appraiser agent

**Role:** Owns `scripts/valuation.py`.  Values guitars in the collection
against current Reverb market data and projects future values using the
era/brand-tier appreciation model.

**Key responsibilities:**
- Reading and writing `data/collection.json`
- Reverb price lookups (via `reverb_price` imported from searcher)
- Appreciation-rate table (`_ERA_RATES`) and compound projection
- Major-brand detection (`MAJOR_BRAND_KEYWORDS`)

**When to invoke this agent:**
- Tuning appreciation rates or adding new brand keywords
- Changes to how collection data is stored or retrieved
- Debugging valuation numbers
