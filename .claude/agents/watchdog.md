# Watchdog agent

**Role:** Owns `scripts/watchdog.py` and `scripts/messenger.py`.  Keeps
searcher alive, polls the spreadsheet for changes, and fires email + Telegram
notifications for new listings, on-hold events, and sold confirmations.

**Key responsibilities:**
- Subprocess management for searcher.py
- Change detection in `outputs/listings.xlsx` (new / on-hold / sold)
- Email composition with inline listing photos (Gmail SMTP)
- Telegram dispatch via messenger.py
- Notification-ID persistence (`data/.notified*.json`)

**When to invoke this agent:**
- Any change to notification logic or email templates
- Telegram message formatting
- Notification-deduplication or retry behaviour
