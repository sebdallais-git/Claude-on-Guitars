<div align="center">

# Vintage Guitar Collector

**AI-powered agentic workflow for vintage guitar hunting, valuation, and collection management**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Claude Code](https://img.shields.io/badge/built_with-Claude_Code-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIgMkw0IDdWMTdMMTIgMjJMMjAgMTdWN0wxMiAyWiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)

Scrapes vintage guitar marketplaces around the clock, scores every listing with a 5-dimension + ML hybrid engine, learns from real market data, and sends you buy recommendations via Telegram and email.

[Quick Start](#-quick-start) | [Dashboard](#-live-dashboard) | [Scoring Model](#-scoring-engine) | [ML System](#-hybrid-ml-scoring)

</div>

---

## How It Works

```
  Retrofret.com ──┐                                    ┌── Telegram alerts
  Woodstore.fr  ──┼──▶ Scraper ──▶ Valuation ──▶ Scorer ──▶ Email alerts
  (more sites)  ──┘      5min       Reverb API    5-dim    Dashboard
                                        │           │
                                        ▼           ▼
                                   Learn agent   ML layer
                                   (daily)       (4 models)
```

Autonomous agents run 24/7 — scraping, valuing, scoring, learning, and notifying. You just check your phone.

---

## Key Features

| | Feature | Details |
|---|---|---|
| **Scraping** | Multi-site monitoring | Retrofret, Woodstore, extensible to any dealer |
| **Valuation** | Reverb market pricing | Real-time lo/mid/hi ranges, currency conversion |
| **Scoring** | 5-dimension engine | Value, Appreciation, Fit, Condition, Iconic status |
| **ML** | Hybrid scoring | 4 models blend with rules as market data accumulates |
| **Learning** | Price history tracking | Daily snapshots, learned appreciation rates |
| **Knowledge** | Curated data | 50 iconic models, 100 top guitarists, 3-tier brands |
| **Dashboard** | Live web UI | Interactive charts, editable budget, knowledge base pages |
| **Alerts** | Real-time notifications | Telegram + email for new listings and recommendations |
| **Budget** | Smart filtering | Editable from dashboard, greys out unaffordable picks |

---

## Quick Start

```bash
# Clone
git clone https://github.com/sebdallais-git/Claude-on-Guitars.git
cd Claude-on-Guitars/vintage-guitar-collector

# Install
pip install requests beautifulsoup4 openpyxl

# Configure
export GMAIL_APP_PASSWORD="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."

# Run
python3 scripts/watchdog.py          # scraper + notifications (24/7)
python3 scripts/scorer.py            # score & rank listings
python3 scripts/dashboard.py         # live dashboard on :8080
```

> **Optional ML deps:** `pip install scikit-learn joblib` to enable the hybrid ML scoring layer.

---

## Live Dashboard

Start the server and access from any device on your network:

```bash
python3 scripts/dashboard.py
# → http://localhost:8080
# → http://YOUR_IP:8080  (iPad, phone)
```

### Pages

| Page | What it shows |
|------|--------------|
| **Dashboard** (`/`) | KPIs, recommendations table, listings, collection, workflow diagram |
| **Scorer** (`/pages/scorer.html`) | Radar chart, dimension weights, boosts, condition scale |
| **Iconic Models** (`/pages/iconic-models.html`) | 50 models with golden era, boost, value range, top artists |
| **Top Guitarists** (`/pages/top-guitarists.html`) | 100 guitarists ranked with their signature guitars |
| **ML Monitor** (`/pages/ml-monitor.html`) | Model status, accuracy charts, score drift, auto-recommendations |

### Interactive Elements

- **Budget card** — click to edit total/spent with +/- controls, saves to `budget.json`
- **Scorer stat cards** — click Iconic Models or Top Guitarists to explore knowledge base
- **Workflow diagram** — click Scorer node to dive into scoring model details
- **Table links** — every listing links back to the dealer page

---

## Scoring Engine

Five dimensions, each 0-100, combined into a weighted composite score:

```
Score = 0.25 * Value + 0.20 * Appreciation + 0.20 * Fit + 0.20 * Condition + 0.15 * Iconic
```

| Dimension | What it measures |
|-----------|-----------------|
| **Value** | Price vs Reverb market range — 100 at or below `reverb_lo`, 0 at 2x `reverb_hi` |
| **Appreciation** | Annual growth rate from era + brand tier + learned rates. +20 golden era boost |
| **Fit** | Collection diversity: +20 new brand, +15 rare type, -25 duplicate, +N iconic boost |
| **Condition** | Mint (100) → Near Mint (95) → Excellent (85) → Very Good (60) → Good (30) → Poor (0) |
| **Iconic** | Rank-weighted count of top-100 guitarists who played this model |

Weights are configurable in `data/budget.json` and visualized as a radar chart on the scorer page.

### Brand Tiers

| Tier | Brands | Appreciation multiplier |
|------|--------|------------------------|
| **Premium** | Fender, Gibson, Martin | Highest |
| **Major** | Rickenbacker, Gretsch, Guild, Epiphone, Taylor, D'Angelico, + 9 more | Medium |
| **Minor** | Everything else | Base |

### Knowledge Base

| File | Entries | Purpose |
|------|---------|---------|
| `iconic_models.json` | 50 models | Golden eras, artist associations, popularity boosts |
| `top_guitarists.json` | 100 guitarists | Rank, name, signature guitars — powers Iconic dimension |
| `brand_tiers.json` | 3 tiers | Premium / Major / Minor classification |

---

## Hybrid ML Scoring

An optional layer that learns from Reverb sold data to improve scoring over time. The rule-based engine stays — ML blends in gradually.

```
Final Score = (1 - ml_blend) * Rule Score + ml_blend * ML Score
```

### 4 Models

| Model | Algorithm | Min Data | What it learns |
|-------|-----------|----------|----------------|
| Weight Optimizer | Ridge Regression | 30 sold | Optimal dimension weights from market outcomes |
| Price Predictor | GradientBoosting | 50 sold | Predicts sold price from 19 features |
| Appreciation Predictor | RandomForest | 20 models | Annual appreciation rate per model |
| Buy/Skip Classifier | GradientBoosting | 30 examples | Buy probability 0-100% |

### Data Pipeline

Runs daily via GitHub Actions:

```
scrape → score → learn → reverb_sold.py → ml_train.py → ml_monitor.py
```

### Cold Start

No sold data yet? The system runs identically to pure rule-based scoring. As data accumulates, models train automatically and the ML blend activates when you're ready:

```json
{
  "ml_enabled": true,
  "ml_blend": 0.3
}
```

---

## Learning Agent

`learn.py` runs daily after scoring:

1. **Snapshots** today's Reverb lo/hi/mid prices per model into `price_history.json`
2. **Computes** annualized appreciation rates from earliest/latest snapshots (min 30 days apart)
3. **Feeds back** into the scorer — learned rates override the static era table

After ~30 days you get your first learned rates. After 3+ months they become reliable market signals.

---

## Configuration

### `data/budget.json`

```json
{
    "total": 20000,
    "spent": 0,
    "weights": {
        "value": 0.25,
        "appreciate": 0.20,
        "fit": 0.20,
        "condition": 0.20,
        "iconic": 0.15
    },
    "top_n": 10,
    "ml_enabled": false,
    "ml_blend": 0.3
}
```

- **total / spent** — editable from the dashboard UI
- **weights** — must sum to 1.0, dimensions activate only if their key exists
- **top_n** — number of recommendations in the Excel sheet
- **ml_enabled / ml_blend** — toggle and tune the ML layer

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GMAIL_APP_PASSWORD` | For email alerts | Gmail App Password (16 chars) |
| `TELEGRAM_BOT_TOKEN` | For Telegram alerts | From @BotFather |
| `TELEGRAM_CHAT_ID` | For Telegram alerts | From @userinfobot |

---

## Project Structure

```
vintage-guitar-collector/
├── scripts/
│   ├── searcher.py             # Multi-site scraper (5-min cycle)
│   ├── watchdog.py             # Keeps scraper alive + notifications
│   ├── scorer.py               # 5-dim scorer with hybrid ML
│   ├── valuation.py            # Reverb pricing + appreciation
│   ├── learn.py                # Daily price snapshots + learned rates
│   ├── dashboard.py            # Live web server on :8080
│   ├── messenger.py            # Telegram Bot API wrapper
│   ├── ml_features.py          # 19-feature extraction
│   ├── ml_train.py             # Trains 4 ML models
│   ├── ml_predict.py           # Inference module
│   ├── ml_monitor.py           # ML vs rule-based comparison
│   ├── reverb_sold.py          # Scrapes Reverb sold listings
│   └── scrapers/               # Site-specific scrapers
│       ├── woodstore.py        #   woodstore.fr (working)
│       ├── guitarpoint.py      #   guitarpoint.de (template)
│       └── rudymusic.py        #   rudymusic.com (template)
├── pages/
│   ├── scorer.html             # Scoring model visualization
│   ├── iconic-models.html      # 50 iconic models browser
│   ├── top-guitarists.html     # Top 100 guitarists browser
│   └── ml-monitor.html         # ML performance dashboard
├── data/
│   ├── budget.json             # Budget + weights + ML config
│   ├── collection.json         # Guitars you own
│   ├── price_history.json      # Reverb price snapshots
│   ├── knowledge/
│   │   ├── brand_tiers.json    # Premium / Major / Minor
│   │   ├── iconic_models.json  # 50 models + golden eras
│   │   └── top_guitarists.json # 100 guitarists + guitars
│   └── ml/                     # ML models + training data
├── outputs/
│   └── listings.xlsx           # Main spreadsheet
├── dashboard.html              # Main dashboard page
├── .github/workflows/          # CI: daily scan + ML pipeline
└── CLAUDE.md                   # Full technical documentation
```

---

## Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| retrofret.com | Working | Full integration, primary source |
| woodstore.fr | Working | Paris dealer, EUR conversion |
| guitarpoint.de | Template | Ready to activate (anti-bot) |
| rudymusic.com | Template | Ready to activate (SSL) |

Adding a new site? See [`scripts/scrapers/README.md`](scripts/scrapers/README.md).

---

## CI / Automation

GitHub Actions runs daily:

```yaml
scrape → score → learn → collect sold data → train ML → monitor
```

The watchdog can also run 24/7 on your Mac via LaunchAgent for real-time monitoring.

---

## Roadmap

- [x] Multi-site scraping (retrofret + woodstore)
- [x] 5-dimension scoring engine
- [x] Hybrid ML scoring (4 models)
- [x] Live dashboard with interactive budget
- [x] Knowledge base pages (iconic models, top guitarists)
- [x] Learning agent with price history
- [x] ML performance monitoring
- [x] Email + Telegram notifications
- [ ] More marketplace integrations
- [ ] Mobile-optimized dashboard
- [ ] Trend analysis & market insights

---

<div align="center">

**Built with [Claude Code](https://claude.ai/claude-code)**

Sebastien DALLAIS — [@sebdallais-git](https://github.com/sebdallais-git)

</div>
