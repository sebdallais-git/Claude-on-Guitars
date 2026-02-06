# 🎸 Vintage Guitar Collector

> An AI-powered agentic workflow that monitors vintage guitar marketplaces, values guitars against market data, and delivers intelligent buy recommendations straight to your inbox.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Multi-Site](https://img.shields.io/badge/Sites-2%2B-green.svg)](#supported-sites)

---

## 📋 Table of Contents

- [Features](#-features)
- [Demo](#-demo)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Dashboard](#-dashboard)
- [Collection Management](#-collection-management)
- [Supported Sites](#-supported-sites)
- [Notifications](#-notifications)
- [Auto-Start Setup](#-auto-start-setup)
- [Project Structure](#-project-structure)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 **Autonomous Scraping**
- Multi-site scraper (retrofret.com, woodstore.fr)
- Runs every 5 minutes automatically
- Condition filtering (≥ excellent-)
- Sold detection with grace period
- Reverb price lookup for each guitar

### 💰 **Smart Valuation**
- Real-time Reverb API integration
- Era-based appreciation forecasting
- Collection valuation tracking
- Currency conversion (EUR ↔ USD)

### 📊 **3-Dimensional Scoring**
- **Value Score** (40%): Price vs Reverb range
- **Appreciation Score** (30%): Annual growth rate
- **Fit Score** (30%): Collection diversity & gaps

### 🔔 **Real-Time Notifications**
- Email alerts for new listings
- Telegram bot integration
- On-hold & sold tracking
- Currency-converted prices

### 📈 **Interactive Dashboard**
- Auto-generated from Excel data
- Clickable workflow diagram
- Brand detail pages (67+ brands)
- Top 10 recommendations
- Market breakdown charts

### 🎯 **Budget Management**
- Configurable spending limit
- Recommendation filtering
- Budget utilization tracking

---

## 🎬 Demo

### Dashboard Overview
The dashboard provides real-time insights into the vintage guitar market:

- **At a Glance KPIs**: Total tracked, active, on-hold, sold, average price
- **Market Breakdown**: Top brands, guitar types, decades, price distribution
- **Top 10 Recommendations**: Scored and ranked by value, appreciation, and fit
- **Interactive Elements**: Click brands → brand pages, click recommendations → detail pages

### Workflow Visualization
```
┌─────────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────────────┐
│ retrofret   │────▶│ Scraper │────▶│ listings.xlsx│────▶│ Watchdog │────▶│ Email + Telegram│
│ woodstore.fr│     │ 5 min   │     │ 471 guitars  │     │          │     │  notifications  │
└─────────────┘     └─────────┘     └──────────────┘     └──────────┘     └─────────────────┘
                                            │
                                            ▼
┌──────────────┐     ┌───────────┐     ┌────────┐
│ collection   │────▶│ Valuation │────▶│ Scorer │────▶ 📊 Recommendations
│    .json     │     │ Reverb API│     │ 3-dim  │
└──────────────┘     └───────────┘     └────────┘
```

---

## 🏗 Architecture

### Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Scraper** | Multi-site crawling | BeautifulSoup, Requests |
| **Watchdog** | Process monitoring + notifications | SMTP, Telegram Bot API |
| **Valuation** | Market pricing + appreciation | Reverb API |
| **Scorer** | 3-dim ranking algorithm | NumPy logic |
| **Dashboard Generator** | HTML from Excel data | OpenPyXL, Jinja-style templating |
| **Currency Module** | EUR ↔ USD conversion | Fixed rates (updateable) |

### Data Flow

1. **Scraper** → Crawls sites → Filters by condition → Writes to Excel
2. **Watchdog** → Monitors Excel → Detects new rows → Sends notifications
3. **Valuation** → Reads collection → Queries Reverb → Forecasts appreciation
4. **Scorer** → Reads listings + collection → Computes scores → Ranks recommendations
5. **Dashboard** → Reads Excel → Generates HTML → Creates detail pages

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip
- Gmail account (for email notifications)
- Telegram bot (optional, for Telegram notifications)

### Installation

```bash
# Clone the repository
git clone https://github.com/sebdallais-git/Claude-on-Guitars.git
cd vintage-guitar-collector

# Install dependencies
pip install requests beautifulsoup4 openpyxl

# Create .env file with credentials
cp .env.example .env
# Edit .env and add your credentials
```

### Configuration

Create `.env` file:

```bash
# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN="your-bot-token-from-@BotFather"
TELEGRAM_CHAT_ID="your-chat-id-from-@userinfobot"

# Gmail App Password
GMAIL_APP_PASSWORD="your-16-char-app-password"
```

### Run

```bash
# Option 1: Run watchdog (keeps scraper alive + sends notifications)
python3 scripts/watchdog.py

# Option 2: Run scraper once
python3 scripts/searcher.py

# Generate dashboard
python3 scripts/generate_dashboard.py
open dashboard.html
```

---

## ⚙️ Configuration

### Budget & Scoring Weights

Edit `data/budget.json`:

```json
{
  "budget": 20000,
  "weights": {
    "value": 0.4,
    "appreciation": 0.3,
    "fit": 0.3
  }
}
```

### Collection Management

Edit `data/collection.json`:

```json
[
  {
    "brand": "Fender",
    "model": "Stratocaster",
    "year": 1963,
    "type": "Electric",
    "condition": "excellent-",
    "finish": "",
    "acquired_date": "2026-02-05",
    "purchase_price": null,
    "notes": ""
  }
]
```

Then run valuation:

```bash
python3 scripts/valuation.py
```

---

## 📖 Usage

### Scraping

```bash
# Multi-site scraper (retrofret + woodstore)
python3 scripts/searcher.py

# Test specific site
python3 scripts/scrapers/woodstore.py
```

### Notifications

```bash
# Start watchdog (email + Telegram)
python3 scripts/watchdog.py

# Test Telegram only
python3 scripts/test_telegram.py

# Test watchdog without sending
python3 scripts/test_watchdog.py
```

### Valuation & Scoring

```bash
# Value your collection
python3 scripts/valuation.py

# Score listings & generate recommendations
python3 scripts/scorer.py
```

### Dashboard

```bash
# Generate dashboard from current data
python3 scripts/generate_dashboard.py

# Open in browser
open dashboard.html
```

---

## 📊 Dashboard

The dashboard provides an interactive overview of the vintage guitar market:

### Features

- **Real-time stats** from `listings.xlsx`
- **Clickable workflow** diagram → recommendations page
- **Clickable brands** → brand-specific listing pages
- **Currency conversion** throughout (EUR ↔ USD)
- **Top 10 recommendations** with scores and projections

### Generation

The dashboard auto-generates from your Excel data:

```bash
python3 scripts/generate_dashboard.py
```

This creates:
- `dashboard.html` - Main overview
- `pages/recommendations.html` - Top picks with details
- `pages/brand-{name}.html` - Per-brand listings (67+ pages)

---

## 🎸 Collection Management

### Add Guitars

Edit `data/collection.json` or use the valuation script:

```bash
# Add guitars to collection.json, then:
python3 scripts/valuation.py
```

### View Valuations

Valuations are automatically calculated based on:
- Reverb price data
- Era-based appreciation rates
- Brand tier (major vs minor)

Example output:

```
Fender Stratocaster 1963  now $17,343  +1y $18,730  +2y $20,228
Gibson Les Paul Custom 1969  now $4,763  +1y $5,001  +2y $5,251
```

### Appreciation Rates

| Era | Major Brand | Minor Brand |
|-----|-------------|-------------|
| Pre-1950 | 10%/yr | 5%/yr |
| 1950-1965 | 8%/yr | 4%/yr |
| 1965-1980 | 5%/yr | 3%/yr |
| 1980-2000 | 3%/yr | 2%/yr |
| 2000+ | 1%/yr | 0%/yr |

**Major brands:** Gibson, Fender, Martin, Taylor, Guild, Rickenbacker, Gretsch, Epiphone, Maccaferri, D'Angelico

---

## 🌐 Supported Sites

| Site | Status | Guitars | Currency | Notes |
|------|--------|---------|----------|-------|
| **retrofret.com** | ✅ Working | 419 | USD | Full integration |
| **woodstore.fr** | ✅ Working | 52 | EUR | Paris-based |
| **rudysmusic.com** | ⚠️ Partial | 33 | USD | Titles/links only |
| **guitarpoint.de** | ❌ Blocked | 0 | EUR | 403 error |

### Adding New Sites

See `scripts/scrapers/README.md` for instructions on adding new marketplaces.

---

## 🔔 Notifications

### Email (Gmail)

1. Create Gmail App Password: https://myaccount.google.com/apppasswords
2. Add to `.env`: `GMAIL_APP_PASSWORD="your-password"`
3. Run watchdog: `python3 scripts/watchdog.py`

### Telegram

1. Create bot via [@BotFather](https://t.me/BotFather)
2. Get chat ID via [@userinfobot](https://t.me/userinfobot)
3. Add to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN="your-token"
   TELEGRAM_CHAT_ID="your-chat-id"
   ```
4. Test: `python3 scripts/test_telegram.py`

### Notification Format

```
[Source] Brand Model Year — Price (Converted) — Condition

Source:    woodstore.fr
Brand:     Gibson
Model:     Les Paul Custom
Year:      1969
Type:      Electric
Price:     €5,000.00 ($5,450.00)
Condition: excellent-

https://woodstore.fr/guitares/p/gibson-les-paul-custom-1969
```

---

## 🔄 Auto-Start Setup

### macOS (LaunchAgent)

Already configured! The watchdog runs automatically on boot.

**Control commands:**

```bash
# Check status
launchctl list | grep vintageguitar

# Stop
launchctl stop com.vintageguitar.watchdog

# Start
launchctl start com.vintageguitar.watchdog

# View logs
tail -f logs/watchdog.log
```

### Linux (systemd)

Create `/etc/systemd/system/vintage-guitar.service`:

```ini
[Unit]
Description=Vintage Guitar Collector Watchdog
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/vintage-guitar-collector
Environment="PATH=/usr/bin:/usr/local/bin"
EnvironmentFile=/path/to/vintage-guitar-collector/.env
ExecStart=/usr/bin/python3 scripts/watchdog.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable vintage-guitar
sudo systemctl start vintage-guitar
sudo systemctl status vintage-guitar
```

---

## 📁 Project Structure

```
vintage-guitar-collector/
├── .claude/                    # Claude agent definitions
│   ├── agents/                 # Role-specific agents
│   ├── skills/                 # Domain knowledge packs
│   └── commands/               # Slash commands
├── .github/workflows/          # CI automation
├── data/                       # Runtime state (gitignored)
│   ├── budget.json             # Budget + weights
│   ├── collection.json         # Your guitars
│   ├── valuations.json         # Valuation cache
│   └── .notified.json          # Notification tracking
├── outputs/                    # Generated files (gitignored)
│   └── listings.xlsx           # Main database
├── pages/                      # Generated HTML pages
│   ├── recommendations.html    # Top picks
│   └── brand-*.html            # Per-brand pages
├── scripts/                    # All Python scripts
│   ├── scrapers/               # Site-specific scrapers
│   │   ├── woodstore.py        # woodstore.fr
│   │   ├── rudymusic.py        # rudysmusic.com
│   │   └── guitarpoint.py      # guitarpoint.de (template)
│   ├── searcher.py             # Multi-site scraper
│   ├── watchdog.py             # Process monitor + notifications
│   ├── messenger.py            # Telegram wrapper
│   ├── currency.py             # EUR ↔ USD conversion
│   ├── valuation.py            # Reverb-based valuation
│   ├── scorer.py               # 3-dim scoring
│   └── generate_dashboard.py  # HTML generator
├── logs/                       # Application logs
├── dashboard.html              # Main dashboard
├── index.html                  # Landing page
└── README.md                   # This file
```

---

## 🗺 Roadmap

### Completed ✅
- [x] Multi-site scraping (retrofret + woodstore)
- [x] Currency conversion (EUR ↔ USD)
- [x] Interactive dashboard
- [x] Email + Telegram notifications
- [x] Collection valuation
- [x] 3-dimensional scoring
- [x] Auto-start on boot (macOS)

### In Progress 🚧
- [ ] rudysmusic.com price extraction
- [ ] guitarpoint.de anti-bot bypass
- [ ] Live currency API integration

### Planned 📋
- [ ] Machine learning price predictions
- [ ] Trend analysis & market insights
- [ ] Mobile app (React Native)
- [ ] Browser extension
- [ ] More marketplace integrations
- [ ] GraphQL API
- [ ] Docker deployment
- [ ] Slack/Discord notifications

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Adding a New Marketplace

1. Create scraper in `scripts/scrapers/your_site.py`
2. Follow the template in `scripts/scrapers/guitarpoint.py`
3. Update `scripts/searcher.py` to import your scraper
4. Test: `python3 scripts/scrapers/your_site.py`
5. Submit PR with documentation

### Development Setup

```bash
# Clone repo
git clone https://github.com/sebdallais-git/Claude-on-Guitars.git
cd vintage-guitar-collector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 scripts/test_*.py
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built with [Claude Code](https://claude.com/claude-code)
- Reverb API for market data
- BeautifulSoup for web scraping
- OpenPyXL for Excel integration

---

## 📧 Contact

**Sebastien DALLAIS**
- Email: sebdallais@gmail.com
- GitHub: [@sebdallais-git](https://github.com/sebdallais-git)

---

## ⚡ Quick Links

- [Setup Guide](SETUP_COMPLETE.md)
- [Project Instructions](CLAUDE.md)
- [Multi-Site Status](scripts/scrapers/SETUP_MULTI_SITE.md)
- [Landing Page](https://sebdallais-git.github.io/Claude-on-Guitars/)

---

<p align="center">
  <strong>Happy hunting! 🎸</strong><br>
  Built with ❤️ and Claude Code
</p>
