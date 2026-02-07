# Vintage Guitar Collector

An automated workflow that scrapes retrofret.com, tracks listings in Excel,
sends real-time notifications (email + Telegram), values guitars against Reverb
price data, scores them for collection fit and investment potential, and
surfaces buy recommendations within a configurable budget.

---

## Quick-start

```bash
# 1. install deps (once)
pip install requests beautifulsoup4 openpyxl

# 2. set env vars (or you will be prompted)
export GMAIL_APP_PASSWORD="…"
export TELEGRAM_BOT_TOKEN="…"
export TELEGRAM_CHAT_ID="…"

# 3. run the scraper + notification loop
python3 scripts/watchdog.py

# 4. (separately) score and refresh recommendations
python3 scripts/scorer.py

# 5. (separately) value your collection against Reverb
python3 scripts/valuation.py
```

---

## Directory layout

```
.
├── .claude/                 # Claude agent / skill / command definitions
│   ├── agents/              # one .md per logical agent role
│   ├── skills/              # domain knowledge packs
│   └── commands/            # slash-command definitions
├── .github/workflows/       # CI automation
├── data/                    # runtime state (gitignored)
│   ├── budget.json          # budget + scoring weights (5-dim)
│   ├── collection.json      # guitars you own
│   ├── watchlist.json       # guitars you are watching
│   ├── valuations.json      # cached valuation results
│   ├── price_history.json   # Reverb price snapshots + learned rates
│   ├── knowledge/           # scoring knowledge base
│   │   ├── brand_tiers.json # premium / major / minor brands
│   │   ├── iconic_models.json # ~50 iconic models with golden eras
│   │   └── top_guitarists.json # top 100 guitarists + guitar associations
│   ├── ml/                  # ML models + training data (gitignored)
│   │   ├── training_data.json  # Reverb sold listings for training
│   │   ├── performance.json    # daily ML vs rule comparison logs
│   │   └── models/             # trained .joblib + *_meta.json
│   ├── listings/retrofret/  # per-site history
│   └── *.json               # scraper caches (.condition_cache, .notified*, etc.)
├── outputs/                 # generated files (gitignored)
│   └── listings.xlsx        # the main spreadsheet
├── scripts/                 # all Python scripts
│   ├── scrapers/            # site-specific scrapers (modular)
│   │   ├── woodstore.py     # woodstore.fr (Paris) - working
│   │   ├── guitarpoint.py   # guitarpoint.de - template (403 blocked)
│   │   ├── rudymusic.py     # rudymusic.com - template (SSL issues)
│   │   ├── README.md        # guide for adding new sites
│   │   ├── SETUP_GUITARPOINT.md  # guitarpoint.de setup instructions
│   │   └── SETUP_MULTI_SITE.md   # status of all scrapers
│   ├── searcher.py          # crawls retrofret every 5 min
│   ├── watchdog.py          # keeps searcher alive, sends notifications
│   ├── messenger.py         # Telegram Bot API wrapper
│   ├── valuation.py         # Reverb-based valuation + 3-tier appreciation model
│   ├── scorer.py            # 5-dim scorer with hybrid ML integration
│   ├── learn.py             # learning agent: snapshots prices, computes rates
│   ├── ml_features.py       # 19-feature extraction for ML models
│   ├── ml_train.py          # trains 4 ML models (weights, price, appreciation, buy/skip)
│   ├── ml_predict.py        # inference: loads models, returns ML scores
│   ├── ml_monitor.py        # daily ML vs rule-based performance tracking
│   ├── reverb_sold.py       # scrapes Reverb sold listings for training data
│   ├── daily-scan.sh        # convenience wrapper for CI
│   ├── notify.sh            # convenience wrapper for notifications
│   └── weekly-report.sh     # placeholder for weekly digest
├── index.html               # (existing)
├── CLAUDE.md                # this file
└── CLAUDE.local.md          # personal overrides (gitignored)
```

---

## Key design decisions

| Decision | Rationale |
|---|---|
| Telegram via raw Bot API | Avoids python-telegram-bot dependency; only `requests` needed |
| Sold-detection grace period | `.sold_candidates.json` timestamps first miss; confirmed only after 600 s (2 scrape cycles) to avoid false positives from transient failures |
| Notification tracking after both channels | Email and Telegram are attempted; ID is marked notified only afterwards, so a partial failure retries next cycle |
| budget.json instead of config.py | JSON is easier to edit programmatically (e.g. from a script or CI) and avoids importing Python |
| collection.json instead of collection.xlsx | Simpler read/write in valuation.py; valuation results are still surfaced in the Excel Recommendations sheet |

---

## Adding new sites

The scraper currently supports retrofret.com. Additional sites can be added using the modular scraper architecture:

1. **Create a new scraper** in `scripts/scrapers/` (use `guitarpoint.py` as template)
2. **Inspect the target site** to find:
   - Category URLs for different guitar types
   - HTML structure and CSS selectors for product listings
   - Product detail page format and condition patterns
3. **Test the scraper** standalone: `python3 scripts/scrapers/your_site.py`
4. **Integrate with watchdog** once working (add import and merge results)

See `scripts/scrapers/SETUP_GUITARPOINT.md` for detailed instructions.

---

## Scoring model (scorer.py)

Five dimensions, each 0-100, weighted-summed to a composite score:

| Dimension | Weight | Logic |
|---|---|---|
| **Value** | 25 % | Price vs Reverb range. 100 at or below `reverb_lo`; drops linearly to 0 at 2x `reverb_hi` |
| **Appreciation** | 20 % | Annual rate (from era + brand-tier table) mapped 0-12 % to 0-100. +20 golden era boost for iconic models |
| **Fit** | 20 % | Base 50. +20 new brand, +15 under-represented type, -25 duplicate brand+model, +N iconic model popularity boost |
| **Condition** | 20 % | Mint=100, Near Mint=95, Excellent=85, Very Good=60, Good=30, Poor=0. Unknown=50 |
| **Iconic** | 15 % | Rank-weighted count of top-100 guitarists who played this model. Score = weighted_count / max * 100 |

Backward-compatible: dimensions only activate if their weight key exists in budget.json.

Rows priced above remaining budget are greyed out in the sheet.

---

## Brand tiers (data/knowledge/brand_tiers.json)

| Tier | Brands |
|---|---|
| **Premium** | Fender, Gibson, Martin |
| **Major** | Rickenbacker, Gretsch, Guild, Epiphone, Taylor, D'Angelico, Maccaferri, National, Dobro, Vox, Mosrite, Harmony, Kay, Danelectro, Supro |
| **Minor** | Everything else |

---

## Appreciation rates (_ERA_RATES in valuation.py)

| Era | Premium brand | Major brand | Minor brand |
|---|---|---|---|
| Pre-1950 | 12 % / yr | 10 % / yr | 5 % / yr |
| 1950-1965 | 10 % | 8 % | 4 % |
| 1965-1980 | 6 % | 5 % | 3 % |
| 1980-2000 | 4 % | 3 % | 2 % |
| 2000+ | 2 % | 1 % | 0 % |

Learned rates from `data/price_history.json` take precedence over the static table when available (requires 30+ days of Reverb snapshots).

---

## Learning agent (learn.py)

Runs daily after scorer.py in the CI pipeline:

1. **Snapshot** — records today's Reverb lo/hi/mid prices per model into `data/price_history.json`
2. **Compute** — annualizes appreciation rates from earliest/latest snapshots (min 30 days apart, clamped to [-20%, +30%])
3. **Feed back** — `appreciation_rate()` checks learned rates first, falls back to static table

After ~30 days of snapshots, the first learned rates become available. After 3+ months, rates become reliable market signals.

---

## Iconic models (data/knowledge/iconic_models.json)

~50 iconic guitar models with:
- **Golden era** year ranges (e.g. 1958-1960 for Les Paul Standard)
- **Artist associations** (Hendrix, Clapton, Page, etc.)
- **Popularity boost** (0-20 points added to Fit score)

When a listing's year falls within its model's golden era, the Appreciation score gets a +20 boost.

---

## Hybrid ML Scoring System

An optional ML layer that learns from market data to improve scoring. The 5-dimension rule-based structure stays — ML adjusts weights and adds predictive signals.

### Architecture

```
Rule-based (5 dims) ──┐
                       ├── Blended Score = (1 - ml_blend) * rule + ml_blend * ML
ML (4 models) ────────┘
```

### Configuration (`data/budget.json`)

| Key | Default | Description |
|-----|---------|-------------|
| `ml_enabled` | `false` | Enable/disable ML scoring |
| `ml_blend` | `0.3` | Blend factor: 0.0 = pure rules, 1.0 = pure ML |

### 4 ML Models (`data/ml/models/`)

| Model | Algorithm | Min Data | What it does |
|-------|-----------|----------|-------------|
| Weight Optimizer | Ridge Regression | 30 sold | Learns optimal dimension weights from sold data |
| Price Predictor | GradientBoosting | 50 sold | Predicts sold price from 15 features |
| Appreciation Predictor | RandomForest | 20 models | Predicts annual appreciation rate |
| Buy/Skip Classifier | GradientBoosting | 30 examples | Buy probability 0-100% |

### Data Pipeline

Daily CI order: scrape → score → learn → collect sold data → train → monitor.

1. `reverb_sold.py` — scrapes Reverb sold listings into `data/ml/training_data.json`
2. `ml_train.py` — trains models (each checks its own data threshold)
3. `ml_monitor.py` — compares ML vs rule-based, writes `data/ml/performance.json`

### Feature Engineering (`ml_features.py`)

19 numeric features extracted from each listing: year, age, price, Reverb range, brand tier, condition, iconic status, guitar type, era bucket, collection overlap.

### Cold Start Behavior

- No models → `scorer.py` runs identically to rule-based (no ML columns)
- `ml_enabled: false` → ML models ignored even if trained
- Models train incrementally as sold data accumulates

### Monitoring (`pages/ml-monitor.html`)

Dashboard page showing: model status, price accuracy (ML vs rules), score drift, buy/skip precision, auto-recommendations for adjusting `ml_blend`.
