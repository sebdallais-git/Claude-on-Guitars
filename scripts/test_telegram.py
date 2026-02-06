#!/usr/bin/env python3
"""
Quick test to send a Telegram message.

Usage:
    export TELEGRAM_BOT_TOKEN="your-token-here"
    export TELEGRAM_CHAT_ID="your-chat-id-here"
    python3 scripts/test_telegram.py
"""

import sys
import os

# Add scripts dir to path so we can import messenger
sys.path.insert(0, os.path.dirname(__file__))

import messenger

def main():
    if not messenger.enabled():
        print("❌ Missing credentials!")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return 1

    print("✓ Credentials found")
    print(f"  Bot token: {messenger._TOKEN[:8]}...")
    print(f"  Chat ID: {messenger._CHAT_ID}")
    print()

    # Test with a simple message
    test_entry = {
        "id": "12345",
        "brand": "Gibson",
        "model": "Les Paul",
        "year": "1959",
        "type": "Electric",
        "price": "$250,000",
        "reverb_low": "$180,000",
        "reverb_hi": "$350,000",
        "condition": "Excellent",
        "url": "https://www.retrofret.com/product/test"
    }

    print("Sending test message...")
    success = messenger.notify_new(test_entry)

    if success:
        print("✅ Test message sent successfully!")
        return 0
    else:
        print("❌ Failed to send message. Check your token/chat ID.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
