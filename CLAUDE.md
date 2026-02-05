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
│   ├── budget.json          # budget + scoring weights
│   ├── collection.json      # guitars you own
│   ├── watchlist.json       # guitars you are watching
│   ├── valuations.json      # cached valuation results
│   ├── listings/retrofret/  # per-site history
│   └── *.json               # scraper caches (.condition_cache, .notified*, etc.)
├── outputs/                 # generated files (gitignored)
│   └── listings.xlsx        # the main spreadsheet
├── scripts/                 # all Python scripts
│   ├── searcher.py          # crawls retrofret every 5 min
│   ├── watchdog.py          # keeps searcher alive, sends notifications
│   ├── messenger.py         # Telegram Bot API wrapper
│   ├── valuation.py         # Reverb-based valuation + appreciation model
│   ├── scorer.py            # scores listings, writes Recommendations sheet
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

## Scoring model (scorer.py)

Three dimensions, each 0-100, weighted-summed to a composite score:

| Dimension | Weight | Logic |
|---|---|---|
| **Value** | 40 % | Price vs Reverb range. 100 at or below `reverb_lo`; drops linearly to 0 at 2x `reverb_hi` |
| **Appreciation** | 30 % | Annual rate (from era + brand-tier table) mapped 0-10 % to 0-100 |
| **Fit** | 30 % | Base 50. +20 new brand, +15 under-represented type, -25 duplicate brand+model |

Rows priced above remaining budget are greyed out in the sheet.

---

## Appreciation rates (_ERA_RATES in valuation.py)

| Era | Major brand | Minor brand |
|---|---|---|
| Pre-1950 | 10 % / yr | 5 % / yr |
| 1950-1965 | 8 % | 4 % |
| 1965-1980 | 5 % | 3 % |
| 1980-2000 | 3 % | 2 % |
| 2000+ | 1 % | 0 % |

Major brands: Gibson, Fender, Martin, Taylor, Guild, Rickenbacker, Gretsch,
Epiphone, Maccaferri, D'Angelico.
