#!/usr/bin/env python3
"""
searcher_multisite — unified scraper for multiple vintage guitar sites

Currently supports:
- retrofret.com (USA, USD)
- woodstore.fr (France, EUR)

Combines results into a single Excel sheet with source column.
"""

import sys
import os

# Add scrapers directory to path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "scrapers"))

# Import existing retrofret scraper logic
import searcher as retrofret_scraper

# Import new site scrapers
import woodstore

def scrape_all_sites():
    """
    Scrape all configured sites and return combined list with source tags.

    Returns:
        list: Combined guitar listings with 'source' field added
    """
    all_guitars = []

    # RetroFret (existing scraper)
    print("\n  [RetroFret] Scraping retrofret.com ...")
    try:
        retrofret_guitars = retrofret_scraper.scrape_all()
        for g in retrofret_guitars:
            g['source'] = 'retrofret.com'
            g['currency'] = 'USD'
        all_guitars.extend(retrofret_guitars)
        print(f"  [RetroFret] Found {len(retrofret_guitars)} guitars")
    except Exception as e:
        print(f"  [RetroFret] Error: {e}")

    # Woodstore.fr
    print("\n  [Woodstore] Scraping woodstore.fr ...")
    try:
        woodstore_guitars = woodstore.scrape_all()
        for g in woodstore_guitars:
            g['source'] = 'woodstore.fr'
            g['currency'] = 'EUR'
        all_guitars.extend(woodstore_guitars)
        print(f"  [Woodstore] Found {len(woodstore_guitars)} guitars")
    except Exception as e:
        print(f"  [Woodstore] Error: {e}")

    return all_guitars


def main():
    """Test the multi-site scraper."""
    print("\n" + "="*80)
    print("  MULTI-SITE VINTAGE GUITAR SCRAPER")
    print("="*80)

    guitars = scrape_all_sites()

    print(f"\n{'='*80}")
    print(f"  TOTAL: {len(guitars)} guitars across all sites")
    print(f"{'='*80}\n")

    # Show breakdown by site
    by_site = {}
    for g in guitars:
        site = g.get('source', 'unknown')
        by_site[site] = by_site.get(site, 0) + 1

    for site, count in by_site.items():
        print(f"  {site:20} {count:3} guitars")
    print()


if __name__ == "__main__":
    main()
