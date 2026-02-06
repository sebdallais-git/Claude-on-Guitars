#!/usr/bin/env python3
"""
Test watchdog multi-site support and currency conversion.

This script tests reading from the Excel file and formatting notifications
without actually sending emails or Telegram messages.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import watchdog

print("\n=== Testing Watchdog Multi-Site Support ===\n")

# Test reading entries from Excel
print("Reading entries from Excel...")
entries = watchdog.read_entries()

if not entries:
    print("❌ No entries found in Excel file")
    sys.exit(1)

print(f"✓ Found {len(entries)} entries\n")

# Group by source
by_source = {}
for entry in entries:
    source = entry.get("source", "unknown")
    by_source.setdefault(source, []).append(entry)

print("Breakdown by source:")
for source, source_entries in by_source.items():
    print(f"  {source:20} {len(source_entries):3} guitars")

print("\n" + "="*80)
print("Sample Entries (with currency conversion):")
print("="*80 + "\n")

# Show 3 samples from each source
for source, source_entries in by_source.items():
    print(f"\n📍 {source.upper()}")
    print("-" * 80)

    for i, entry in enumerate(source_entries[:3], 1):
        print(f"\n{i}. {entry['brand']} {entry['model']} ({entry['year']})")
        print(f"   Price: {entry.get('price_converted', entry['price'])}")
        print(f"   Condition: {entry['condition']}")
        print(f"   URL: {entry['url'][:60]}...")

print("\n" + "="*80)
print("Email Subject Line Samples:")
print("="*80 + "\n")

# Test email message formatting
for source, source_entries in by_source.items():
    if source_entries:
        entry = source_entries[0]
        # Build a sample message
        source_name = source.replace(".com", "").replace(".fr", "").title()
        subject = (
            f"[{source_name}] {entry['brand']} {entry['model']} "
            f"{entry['year']} — {entry.get('price_converted', entry['price'])} — {entry['condition']}"
        )
        print(f"• {subject}")

print("\n✅ Watchdog multi-site test complete!\n")
print("To test actual notifications:")
print("  1. Make sure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in .env")
print("  2. Run: python3 scripts/watchdog.py")
print()
