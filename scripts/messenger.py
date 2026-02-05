#!/usr/bin/env python3
"""
messenger — Telegram notifications for new, on-hold, and sold guitars.

Uses the Telegram Bot API directly over HTTPS — no extra dependencies
beyond requests (already a project dependency).

Required env vars:
    TELEGRAM_BOT_TOKEN   — from @BotFather
    TELEGRAM_CHAT_ID     — your personal chat ID
"""

import os
import requests

_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
_API     = "https://api.telegram.org"

# RetroFret product-photo URL pattern
PHOTO_URL = "https://www.retrofret.com/images/{pid}_Guitar/{pid}_01.jpg"


def enabled():
    """True when both TOKEN and CHAT_ID are set."""
    return bool(_TOKEN and _CHAT_ID)


# ── low-level ─────────────────────────────────────────────────────
def _post(endpoint, payload):
    """POST to the Telegram Bot API.  Returns True on success."""
    try:
        resp = requests.post(
            f"{_API}/bot{_TOKEN}/{endpoint}",
            json=payload,
            timeout=10,
        )
        return resp.ok
    except Exception:
        return False


def _details(entry):
    """Shared detail block (HTML)."""
    lines = [
        f"<b>{entry['brand']} {entry['model']} {entry['year']}</b>",
        f"Type:      {entry['type']}",
        f"Price:     {entry['price']}",
    ]
    if entry.get("reverb_low") and entry["reverb_low"] != "N/A":
        lines.append(f"Reverb:    {entry['reverb_low']} – {entry['reverb_hi']}")
    lines.append(f"Condition: {entry['condition']}")
    lines.append(f'\n<a href="{entry["url"]}">View on RetroFret</a>')
    return "\n".join(lines)


def _send(caption, pid=None):
    """Send photo + caption when pid is given; falls back to text-only."""
    if pid:
        photo_url = PHOTO_URL.format(pid=pid)
        if _post("sendPhoto", {
            "chat_id":    _CHAT_ID,
            "photo":      photo_url,
            "caption":    caption,
            "parse_mode": "HTML",
        }):
            return True
    # text-only (fallback or sold notifications)
    return _post("sendMessage", {
        "chat_id":    _CHAT_ID,
        "text":       caption,
        "parse_mode": "HTML",
    })


# ── public API ────────────────────────────────────────────────────
def notify_new(entry):
    """[NEW] listing alert with photo."""
    return _send(f"[NEW]\n\n{_details(entry)}", pid=entry["id"])


def notify_on_hold(entry):
    """[ON HOLD] alert with photo."""
    return _send(f"[ON HOLD]\n\n{_details(entry)}", pid=entry["id"])


def notify_sold(entry):
    """[SOLD] alert — text only (listing is gone)."""
    return _send(f"[SOLD]\n\n{_details(entry)}")
