# 🎸 Vintage Guitar Collector - Setup Complete!

## ✅ System Status

### **Watchdog Service** - Running ✓
- **Status:** Active and monitoring
- **Auto-start:** Enabled (runs on boot)
- **Process:** LaunchAgent `com.vintageguitar.watchdog`
- **Logs:** `logs/watchdog.log` and `logs/watchdog.error.log`

### **Multi-Site Scraper** - Running ✓
- **Sites:** retrofret.com + woodstore.fr
- **Frequency:** Every 5 minutes
- **Currently tracking:** 211 guitars
- **Format:** Excel with Source column + currency info

### **Notifications** - Configured ✓
- **Email:** sebdallais@gmail.com (Gmail App Password stored)
- **Telegram:** Bot configured (tested working)
- **Triggers:** New listings, On Hold, Sold

### **Collection** - Valued ✓
- **Guitars:** 8 vintage pieces
- **Current Value:** $45,656
- **Projected (2y):** $53,176 (+16.5%)

---

## 🔄 Auto-Start Configuration

### LaunchAgent Location
```
~/Library/LaunchAgents/com.vintageguitar.watchdog.plist
```

### What Runs on Boot
1. Watchdog loads environment from `.env`
2. Launches multi-site scraper (`searcher.py`)
3. Monitors Excel for new/changed listings
4. Sends notifications via Email + Telegram
5. Auto-restarts if it crashes (60s throttle)

### Control Commands
```bash
# Check status
launchctl list | grep vintageguitar

# Stop service
launchctl stop com.vintageguitar.watchdog

# Start service
launchctl start com.vintageguitar.watchdog

# Restart service
launchctl stop com.vintageguitar.watchdog && launchctl start com.vintageguitar.watchdog

# Unload (disable auto-start)
launchctl unload ~/Library/LaunchAgents/com.vintageguitar.watchdog.plist

# Reload (re-enable auto-start)
launchctl load ~/Library/LaunchAgents/com.vintageguitar.watchdog.plist
```

---

## 📊 Dashboard

### Generate Dashboard
```bash
python3 scripts/generate_dashboard.py
open dashboard.html
```

### Features
- Real-time stats from Excel
- Clickable workflow diagram
- Brand pages (67 brands)
- Recommendations with details
- Currency conversion (EUR ↔ USD)

---

## 📁 Key Files

### Configuration
- `.env` - Credentials (gitignored)
- `data/budget.json` - Budget and scoring weights
- `data/collection.json` - Your guitars + valuations

### Data
- `outputs/listings.xlsx` - Main database
- `data/.notified.json` - Notification tracking
- `data/.condition_cache.json` - Condition cache

### Logs
- `logs/watchdog.log` - Main log
- `logs/watchdog.error.log` - Errors only

---

## 🎯 What Happens Next

### Every 5 Minutes
1. **Scraper** crawls retrofret.com + woodstore.fr
2. **Filters** by condition (≥ excellent-)
3. **Updates** Excel with new listings
4. **Lookups** Reverb prices for new guitars
5. **Watchdog** detects new rows
6. **Sends** Email + Telegram notifications
7. **Marks** sold guitars after grace period

### Manual Tasks
- **Update dashboard:** `python3 scripts/generate_dashboard.py`
- **Value collection:** `python3 scripts/valuation.py`
- **Score listings:** `python3 scripts/scorer.py`
- **View logs:** `tail -f logs/watchdog.log`

---

## 🚨 Troubleshooting

### Check if running
```bash
ps aux | grep -E "watchdog|searcher" | grep python
```

### View live logs
```bash
tail -f logs/watchdog.log
```

### Test notifications
1. Delete a few IDs from `data/.notified.json`
2. Restart: `launchctl restart com.vintageguitar.watchdog`
3. Check log for notification attempts

### Email not working?
- Verify Gmail App Password in `.env`
- Check `logs/watchdog.error.log`
- Test: https://myaccount.google.com/apppasswords

### Telegram not working?
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Test: `python3 scripts/test_telegram.py`

---

## 📈 Next Steps

1. **Monitor logs** for first few hours
2. **Test notifications** by deleting notified IDs
3. **Generate dashboard** to see all data
4. **Run scorer** to see recommendations
5. **Check GitHub Actions** for daily scan

---

## 🎸 Your Collection

| Guitar | Year | Value | +2 Years |
|--------|------|-------|----------|
| Fender Stratocaster | 1963 | $17,343 | $20,228 |
| Fender Jazz Bass | 1963 | $8,297 | $9,678 |
| Gibson SG Special | 1961 | $4,583 | $5,346 |
| Gibson Les Paul Custom | 1969 | $4,763 | $5,251 |
| Fender Jaguar | 1964 | $3,551 | $4,141 |
| Gibson ES-330 | 1964 | $3,266 | $3,809 |
| Fender Jazz Bass | 1974 | $2,294 | $2,529 |
| Gibson Les Paul R9 | 2005 | $1,560 | $1,592 |

**Total:** $45,656 → $52,687 (projected 2y)

---

## 🔐 Security

- `.env` is gitignored (credentials safe)
- LaunchAgent runs as your user (not root)
- Logs rotate automatically
- No sensitive data in git

---

Built with Claude Code 🤖
Last updated: 2026-02-06
