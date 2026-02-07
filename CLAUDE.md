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
│   ├── budget.json          # budget + scoring weights (4-dim)
│   ├── collection.json      # guitars you own
│   ├── watchlist.json       # guitars you are watching
│   ├── valuations.json      # cached valuation results
│   ├── price_history.json   # Reverb price snapshots + learned rates
│   ├── knowledge/           # scoring knowledge base
│   │   ├── brand_tiers.json # premium / major / minor brands
│   │   └── iconic_models.json # ~50 iconic models with golden eras
│   ├── listings/retrofret/  # per-site history
│   └── *.json               # scraper caches (.condition_cache, .notified*, etc.)
├── outputs/                 # generated files (gitignored)
│   └── listings.xlsx        # the main spreadsheet
├── scripts/                 # all Python scripts
│   ├── scrapers/            # site-specific scrapers (modular)
│   │   ├── woodstore.py     # ✅ woodstore.fr (Paris) - working
│   │   ├── guitarpoint.py   # ⚠️ guitarpoint.de - template (403 blocked)
│   │   ├── rudymusic.py     # ⚠️ rudymusic.com - template (SSL issues)
│   │   ├── README.md        # guide for adding new sites
│   │   ├── SETUP_GUITARPOINT.md  # guitarpoint.de setup instructions
│   │   └── SETUP_MULTI_SITE.md   # status of all scrapers
│   ├── searcher.py          # crawls retrofret every 5 min
│   ├── watchdog.py          # keeps searcher alive, sends notifications
│   ├── messenger.py         # Telegram Bot API wrapper
│   ├── valuation.py         # Reverb-based valuation + 3-tier appreciation model
│   ├── scorer.py            # 4-dim scorer with knowledge base integration
│   ├── learn.py             # learning agent: snapshots prices, computes rates
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

Four dimensions, each 0-100, weighted-summed to a composite score:

| Dimension | Weight | Logic |
|---|---|---|
| **Value** | 30 % | Price vs Reverb range. 100 at or below `reverb_lo`; drops linearly to 0 at 2x `reverb_hi` |
| **Appreciation** | 25 % | Annual rate (from era + brand-tier table) mapped 0-12 % to 0-100. +20 golden era boost for iconic models |
| **Fit** | 25 % | Base 50. +20 new brand, +15 under-represented type, -25 duplicate brand+model, +N iconic model popularity boost |
| **Condition** | 20 % | Mint=100, Near Mint=95, Excellent=85, Very Good=60, Good=30, Poor=0. Unknown=50 |

Backward-compatible: if `condition` weight is missing from budget.json, uses old 3-dim formula.

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
