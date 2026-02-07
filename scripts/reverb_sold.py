#!/usr/bin/env python3
"""
reverb_sold — scrapes sold listings from Reverb for ML training data.

Queries the Reverb API for completed/sold transactions, extracting price
and condition data to train the ML scoring models.

Data stored in data/ml/training_data.json.

Usage:
    python3 scripts/reverb_sold.py
"""

import json
import os
import sys
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

# Reuse the same headers as searcher.py for consistency
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

REVERB_HEADERS = {
    **HTTP_HEADERS,
    "Accept": "application/hal+json",
    "Accept-Version": "3.0",
}

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA         = os.path.join(_PROJECT_ROOT, "data")
_ML_DIR       = os.path.join(_DATA, "ml")
TRAINING_FILE = os.path.join(_ML_DIR, "training_data.json")
PRICE_HISTORY = os.path.join(_DATA, "price_history.json")

# Rate limit: seconds between API calls
RATE_LIMIT = 0.5


def _load_training_data():
    """Load existing training data or create fresh structure."""
    if os.path.exists(TRAINING_FILE):
        try:
            with open(TRAINING_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    return {"version": 1, "last_updated": None, "sold_listings": [], "user_decisions": []}


def _save_training_data(data):
    """Save training data to disk."""
    os.makedirs(_ML_DIR, exist_ok=True)
    data["last_updated"] = date.today().isoformat()
    with open(TRAINING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _get_model_queries():
    """Get unique brand|model keys from price_history.json.

    Returns list of (brand, model) tuples.
    """
    if not os.path.exists(PRICE_HISTORY):
        return []

    try:
        with open(PRICE_HISTORY) as f:
            history = json.load(f)
    except (json.JSONDecodeError, KeyError):
        return []

    queries = []
    for key in history.get("snapshots", {}):
        parts = key.split("|", 1)
        if len(parts) == 2:
            brand, model = parts
            queries.append((brand.strip(), model.strip()))

    return queries


def _fetch_sold_listings(brand, model, per_page=25):
    """Fetch one page of sold listings from Reverb API.

    Returns list of parsed listing dicts, or empty list on failure.
    """
    query = f"{brand} {model}"
    try:
        resp = requests.get(
            "https://api.reverb.com/api/listings/all",
            params={"state": "sold", "query": query, "per_page": per_page},
            headers=REVERB_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"    API error for {query}: {e}")
        return []

    results = []
    for item in data.get("listings", []):
        listing_id = item.get("id")
        if not listing_id:
            continue

        # Extract price info
        price_obj = item.get("price", {})
        listed_price = None
        if price_obj:
            try:
                listed_price = float(price_obj.get("amount", 0))
            except (ValueError, TypeError):
                pass

        # Condition
        condition = item.get("condition", {})
        condition_str = condition.get("display_name", "") if isinstance(condition, dict) else str(condition)

        # Year from title parsing
        title = item.get("title", "")
        year_str = ""
        import re
        m = re.search(r"\b(19\d{2}|20[0-2]\d)\b", title)
        if m:
            year_str = m.group(0)

        # Guitar type from categories
        guitar_type = "Electric"
        categories = item.get("categories", [])
        for cat in categories:
            cat_name = cat.get("full_name", "").lower() if isinstance(cat, dict) else ""
            if "acoustic" in cat_name:
                guitar_type = "Acoustic"
            elif "bass" in cat_name:
                guitar_type = "Bass"

        results.append({
            "id": f"reverb_{listing_id}",
            "brand": brand.title(),
            "model": model.title(),
            "year": year_str,
            "type": guitar_type,
            "condition": condition_str,
            "listed_price": listed_price,
            "sold_price": listed_price,  # Reverb API doesn't always expose final sold price
            "reverb_lo": None,  # filled in if we have price history
            "reverb_hi": None,
            "sold_date": item.get("created_at", "")[:10],
            "source": "reverb_sold",
        })

    return results


def _enrich_with_reverb_range(listings, price_history):
    """Add reverb_lo / reverb_hi from price history where available."""
    snapshots = price_history.get("snapshots", {})

    for listing in listings:
        key = f"{listing['brand'].lower()}|{listing['model'].lower()}"
        if key in snapshots and snapshots[key]:
            latest = snapshots[key][-1]
            listing["reverb_lo"] = latest.get("reverb_lo")
            listing["reverb_hi"] = latest.get("reverb_hi")


def collect():
    """Main collection routine. Fetches sold data for all known models."""
    print("  Reverb Sold Data Collector")
    print("  " + "=" * 40)

    queries = _get_model_queries()
    if not queries:
        print("  No models in price_history.json — run scorer.py first to build price data.")
        print("  Skipping collection.")
        return

    # Load price history for enrichment
    price_history = {}
    if os.path.exists(PRICE_HISTORY):
        try:
            with open(PRICE_HISTORY) as f:
                price_history = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    data = _load_training_data()
    existing_ids = {l["id"] for l in data["sold_listings"]}

    print(f"  Models to query:     {len(queries)}")
    print(f"  Existing sold data:  {len(data['sold_listings'])} listings")
    print()

    new_count = 0
    errors = 0

    for i, (brand, model) in enumerate(queries):
        print(f"  [{i+1}/{len(queries)}] {brand} {model} ... ", end="", flush=True)

        sold = _fetch_sold_listings(brand, model)
        if not sold:
            print("0 results")
            errors += 1
            time.sleep(RATE_LIMIT)
            continue

        # Enrich with Reverb price ranges
        _enrich_with_reverb_range(sold, price_history)

        # Deduplicate
        added = 0
        for listing in sold:
            if listing["id"] not in existing_ids:
                data["sold_listings"].append(listing)
                existing_ids.add(listing["id"])
                added += 1

        print(f"{added} new / {len(sold)} fetched")
        new_count += added
        time.sleep(RATE_LIMIT)

    _save_training_data(data)

    print()
    print(f"  Collection complete:")
    print(f"    New listings added: {new_count}")
    print(f"    Total sold data:   {len(data['sold_listings'])}")
    print(f"    API errors:        {errors}")
    print(f"    Saved to:          {TRAINING_FILE}")


if __name__ == "__main__":
    collect()
