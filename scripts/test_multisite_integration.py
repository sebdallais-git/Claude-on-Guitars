#!/usr/bin/env python3
"""Quick test of multi-site searcher integration."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import searcher

print("\n=== Testing Multi-Site Searcher Integration ===\n")

# Test scrape_all()
print("Running scrape_all() ...")
guitars = searcher.scrape_all()

print(f"\nTotal guitars found: {len(guitars)}")

# Count by source
by_source = {}
for g in guitars:
    source = g.get('source', 'unknown')
    by_source[source] = by_source.get(source, 0) + 1

print("\nBreakdown by source:")
for source, count in by_source.items():
    print(f"  {source:20} {count:3} guitars")

# Show a few samples
print("\nSample listings:")
for i, g in enumerate(guitars[:5], 1):
    print(f"{i}. [{g.get('source', '?')}] {g['title'][:60]} - {g['price']}")

print("\n✅ Integration test complete!")
