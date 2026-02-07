#!/usr/bin/env python3
"""
learn — snapshot Reverb prices and compute learned appreciation rates.

Reads active listings from listings.xlsx, records today's Reverb prices
into data/price_history.json, then computes annualized rates from the
accumulated snapshots (requires 30+ days of data).

Run standalone:
    python3 learn.py

Designed to run daily after scorer.py in the CI pipeline.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scorer import read_active_listings
from valuation import snapshot_prices, compute_learned_rates


def run():
    """Snapshot today's prices and recompute learned rates."""
    listings = read_active_listings()

    if not listings:
        print("  No active listings found — nothing to learn from.")
        return

    # Step 1: record today's Reverb prices
    snap_count = snapshot_prices(listings)
    print(f"  Snapshots:       {snap_count} new price points recorded")

    # Step 2: recompute rates from accumulated history
    rate_count = compute_learned_rates(min_days=30)
    if rate_count:
        print(f"  Learned rates:   {rate_count} models with computed rates")
    else:
        print(f"  Learned rates:   none yet (need 30+ days of snapshots)")

    print(f"  Done — price_history.json updated")


if __name__ == "__main__":
    run()
