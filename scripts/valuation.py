#!/usr/bin/env python3
"""
valuation — current + projected values for guitars in collection.json.

Uses Reverb price guide for current market value, then applies a
simple era / brand-tier appreciation model for 1-year and 2-year
projections.  Rates are approximate historical averages for the
vintage guitar market — tune the _ERA_RATES table below as needed.

Run standalone to refresh all valuations:
    python3 valuation.py
"""

import json
import os
import re
import sys
from datetime import date
from concurrent.futures import ThreadPoolExecutor

# ensure local imports resolve regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from searcher import reverb_price          # reuse existing Reverb lookup

# ── config ────────────────────────────────────────────────────────
_SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT   = os.path.dirname(_SCRIPT_DIR)
_DATA           = os.path.join(_PROJECT_ROOT, "data")
COLLECTION_FILE = os.path.join(_DATA, "collection.json")


# ── appreciation model ───────────────────────────────────────────
# Keywords that identify a "major" brand (matched against any word in the name).
MAJOR_BRAND_KEYWORDS = {
    "gibson", "fender", "martin", "taylor", "guild",
    "rickenbacker", "gretsch", "epiphone", "maccaferri", "angelico",
}

# Annual appreciation rates: (era_start, era_end, rate_major, rate_minor).
# These are approximate historical averages.  Adjust as you observe the market.
_ERA_RATES = [
    (0,    1950, 0.10, 0.05),   # pre-war / early post-war
    (1950, 1965, 0.08, 0.04),   # golden era
    (1965, 1980, 0.05, 0.03),   # classic era
    (1980, 2000, 0.03, 0.02),   # modern vintage
    (2000, 9999, 0.01, 0.00),   # recent
]


def _is_major(brand):
    """True when any word in `brand` matches a major-brand keyword."""
    words = set(re.split(r"[^a-z]+", brand.lower())) - {""}
    return bool(words & MAJOR_BRAND_KEYWORDS)


def _parse_year(raw):
    """Extract first 4-digit year from strings like '1965', 'c.1965', '1960s'."""
    m = re.search(r"\d{4}", str(raw))
    return int(m.group(0)) if m else None


def appreciation_rate(brand, year):
    """Return estimated annual appreciation rate (e.g. 0.08 = 8 %)."""
    yr   = _parse_year(year) or 1970
    tier = "major" if _is_major(brand) else "minor"
    for start, end, major_rate, minor_rate in _ERA_RATES:
        if start <= yr < end:
            return major_rate if tier == "major" else minor_rate
    return 0.02  # fallback


def project_value(current_value, brand, year, years_ahead):
    """Compound appreciation from *current_value* over *years_ahead*."""
    if current_value is None or current_value <= 0:
        return None
    rate = appreciation_rate(brand, year)
    return round(current_value * ((1 + rate) ** years_ahead), 2)


# ── core valuation ────────────────────────────────────────────────
def value_guitar(brand, model, year):
    """
    Query Reverb and project future values.
    Returns dict: current, value_1y, value_2y, reverb_lo, reverb_hi.
    All values are None when Reverb has no data.
    """
    rev_lo, rev_hi = reverb_price(brand, model, str(year))
    current = round((rev_lo + rev_hi) / 2, 2) if rev_lo else None
    return {
        "current":   current,
        "value_1y":  project_value(current, brand, year, 1),
        "value_2y":  project_value(current, brand, year, 2),
        "reverb_lo": rev_lo,
        "reverb_hi": rev_hi,
    }


# ── JSON I/O ──────────────────────────────────────────────────────
def read_collection():
    """Return list of guitar dicts from collection.json."""
    if not os.path.exists(COLLECTION_FILE):
        return []
    with open(COLLECTION_FILE) as f:
        return json.load(f)


def _save_collection(guitars):
    with open(COLLECTION_FILE, "w") as f:
        json.dump(guitars, f, indent=2)


def update_collection():
    """Read collection.json, value every guitar via Reverb, write back."""
    if not os.path.exists(COLLECTION_FILE):
        _save_collection([])
        print(f"  Created {COLLECTION_FILE}")
        print("  Add your guitars as JSON objects, then run again:  python3 valuation.py")
        return

    guitars = read_collection()
    # keep only entries that have enough info to value
    to_value = [(i, g) for i, g in enumerate(guitars)
                if g.get("brand") and g.get("model") and g.get("year")]

    if not to_value:
        print("  Nothing to value — add guitars to collection.json first.")
        return

    print(f"  Valuing {len(to_value)} guitars …")
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(value_guitar, g["brand"], g["model"], g["year"])
                   for _, g in to_value]
        results = [f.result() for f in futures]

    today = date.today().isoformat()
    for (idx, g), vals in zip(to_value, results):
        if vals["current"] is not None:
            guitars[idx]["current_value"] = vals["current"]
            guitars[idx]["value_1y"]      = vals["value_1y"]
            guitars[idx]["value_2y"]      = vals["value_2y"]
            guitars[idx]["last_updated"]  = today
            print(f"  {g['brand']:22} {g['model']:24} {g['year']:>8}  "
                  f"now ${vals['current']:>10,.0f}  "
                  f"+1y ${vals['value_1y']:>10,.0f}  "
                  f"+2y ${vals['value_2y']:>10,.0f}")
        else:
            print(f"  {g['brand']:22} {g['model']:24} {g['year']:>8}  — no Reverb data")

    _save_collection(guitars)
    print(f"\n  Saved → {COLLECTION_FILE}")


if __name__ == "__main__":
    update_collection()
