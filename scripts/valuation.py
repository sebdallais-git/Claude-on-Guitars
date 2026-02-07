#!/usr/bin/env python3
"""
valuation — current + projected values for guitars in collection.json.

Uses Reverb price guide for current market value, then applies an
era / brand-tier appreciation model for 1-year and 2-year projections.

Brand tiers (premium / major / minor) are loaded from
data/knowledge/brand_tiers.json, falling back to hardcoded defaults.
Learned appreciation rates from data/price_history.json take precedence
over the static table when available.

Run standalone to refresh all valuations:
    python3 valuation.py
"""

import json
import math
import os
import re
import sys
from datetime import date
from concurrent.futures import ThreadPoolExecutor

# ensure local imports resolve regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from searcher import reverb_price          # reuse existing Reverb lookup

# ── config ────────────────────────────────────────────────────────
_SCRIPT_DIR      = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT    = os.path.dirname(_SCRIPT_DIR)
_DATA            = os.path.join(_PROJECT_ROOT, "data")
COLLECTION_FILE  = os.path.join(_DATA, "collection.json")
_KNOWLEDGE_DIR   = os.path.join(_DATA, "knowledge")
_BRAND_TIERS_FILE = os.path.join(_KNOWLEDGE_DIR, "brand_tiers.json")
_PRICE_HISTORY   = os.path.join(_DATA, "price_history.json")


# ── brand tiers ───────────────────────────────────────────────────
# Hardcoded fallback when JSON is missing
_DEFAULT_PREMIUM = {"fender", "gibson", "martin"}
_DEFAULT_MAJOR = {
    "rickenbacker", "gretsch", "guild", "epiphone", "taylor",
    "angelico", "maccaferri", "national", "dobro", "vox",
    "mosrite", "harmony", "kay", "danelectro", "supro",
}

# Legacy keyword set kept for backward compatibility
MAJOR_BRAND_KEYWORDS = {
    "gibson", "fender", "martin", "taylor", "guild",
    "rickenbacker", "gretsch", "epiphone", "maccaferri", "angelico",
}

_brand_tier_cache = None


def _load_brand_tiers():
    """Load 3-tier brand data from JSON, falling back to hardcoded defaults."""
    global _brand_tier_cache
    if _brand_tier_cache is not None:
        return _brand_tier_cache

    premium = set(_DEFAULT_PREMIUM)
    major = set(_DEFAULT_MAJOR)

    if os.path.exists(_BRAND_TIERS_FILE):
        try:
            with open(_BRAND_TIERS_FILE) as f:
                data = json.load(f)
            premium = {b.lower() for b in data.get("premium", [])}
            major = {b.lower() for b in data.get("major", [])}
        except (json.JSONDecodeError, KeyError):
            pass  # fall back to defaults

    _brand_tier_cache = (premium, major)
    return _brand_tier_cache


def _brand_tier(brand):
    """Return 'premium', 'major', or 'minor' for a brand string."""
    premium, major = _load_brand_tiers()
    # Match any word in the brand name (handles "D'Angelico" → "angelico")
    words = set(re.split(r"[^a-z]+", brand.lower())) - {""}
    if words & premium:
        return "premium"
    if words & major:
        return "major"
    return "minor"


def _is_major(brand):
    """True when brand is premium or major. Kept for backward compatibility."""
    return _brand_tier(brand) in ("premium", "major")


# ── appreciation model ───────────────────────────────────────────
# Annual rates: (era_start, era_end, rate_premium, rate_major, rate_minor)
_ERA_RATES = [
    (0,    1950, 0.12, 0.10, 0.05),   # pre-war / early post-war
    (1950, 1965, 0.10, 0.08, 0.04),   # golden era
    (1965, 1980, 0.06, 0.05, 0.03),   # classic era
    (1980, 2000, 0.04, 0.03, 0.02),   # modern vintage
    (2000, 9999, 0.02, 0.01, 0.00),   # recent
]


def _parse_year(raw):
    """Extract first 4-digit year from strings like '1965', 'c.1965', '1960s'."""
    m = re.search(r"\d{4}", str(raw))
    return int(m.group(0)) if m else None


# ── learned rates ─────────────────────────────────────────────────
_learned_rates_cache = None


def _load_learned_rates():
    """Load learned appreciation rates from price_history.json."""
    global _learned_rates_cache
    if _learned_rates_cache is not None:
        return _learned_rates_cache

    _learned_rates_cache = {}
    if os.path.exists(_PRICE_HISTORY):
        try:
            with open(_PRICE_HISTORY) as f:
                data = json.load(f)
            _learned_rates_cache = data.get("learned_rates", {})
        except (json.JSONDecodeError, KeyError):
            pass

    return _learned_rates_cache


def appreciation_rate(brand, year, model=None):
    """Return estimated annual appreciation rate (e.g. 0.08 = 8 %).

    If a learned rate exists for the brand+model combination, it takes
    precedence over the static era table.
    """
    # Check learned rates first (keyed by "brand|model" lowercase)
    if model:
        learned = _load_learned_rates()
        key = f"{brand.lower()}|{model.lower()}"
        if key in learned:
            return learned[key]

    yr = _parse_year(year) or 1970
    tier = _brand_tier(brand)

    for start, end, rate_premium, rate_major, rate_minor in _ERA_RATES:
        if start <= yr < end:
            if tier == "premium":
                return rate_premium
            elif tier == "major":
                return rate_major
            else:
                return rate_minor
    return 0.02  # fallback


# ── price snapshots for learning ─────────────────────────────────
def snapshot_prices(listings):
    """Append today's Reverb price data to price_history.json.

    Each listing should have brand, model, reverb_lo, reverb_hi keys.
    Only records entries that have valid Reverb data.
    """
    today = date.today().isoformat()

    history = {"snapshots": {}, "learned_rates": {}}
    if os.path.exists(_PRICE_HISTORY):
        try:
            with open(_PRICE_HISTORY) as f:
                history = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    snapshots = history.setdefault("snapshots", {})
    count = 0

    for listing in listings:
        lo = listing.get("reverb_lo")
        hi = listing.get("reverb_hi")
        if lo is None or hi is None:
            continue

        brand = listing.get("brand", "").strip()
        model = listing.get("model", "").strip()
        if not brand or not model:
            continue

        key = f"{brand.lower()}|{model.lower()}"
        if key not in snapshots:
            snapshots[key] = []

        # Don't duplicate same-day snapshots
        if snapshots[key] and snapshots[key][-1]["date"] == today:
            continue

        snapshots[key].append({
            "date": today,
            "reverb_lo": lo,
            "reverb_hi": hi,
            "mid": round((lo + hi) / 2, 2),
        })
        count += 1

    os.makedirs(os.path.dirname(_PRICE_HISTORY), exist_ok=True)
    with open(_PRICE_HISTORY, "w") as f:
        json.dump(history, f, indent=2)

    return count


def compute_learned_rates(min_days=30):
    """Compute annualized appreciation rates from price snapshots.

    Requires at least `min_days` between earliest and latest snapshot
    for a given model. Rates are clamped to [-20%, +30%].
    Returns number of models with computed rates.
    """
    if not os.path.exists(_PRICE_HISTORY):
        return 0

    with open(_PRICE_HISTORY) as f:
        history = json.load(f)

    snapshots = history.get("snapshots", {})
    learned = {}
    count = 0

    for key, points in snapshots.items():
        if len(points) < 2:
            continue

        earliest = points[0]
        latest = points[-1]

        d0 = date.fromisoformat(earliest["date"])
        d1 = date.fromisoformat(latest["date"])
        days = (d1 - d0).days

        if days < min_days:
            continue

        mid0 = earliest["mid"]
        mid1 = latest["mid"]

        if mid0 <= 0:
            continue

        # Annualize: rate = (final/initial)^(365/days) - 1
        ratio = mid1 / mid0
        years = days / 365.0
        annual_rate = math.pow(ratio, 1.0 / years) - 1.0

        # Clamp to [-20%, +30%] to avoid wild extrapolations
        annual_rate = max(-0.20, min(0.30, annual_rate))
        learned[key] = round(annual_rate, 4)
        count += 1

    history["learned_rates"] = learned

    with open(_PRICE_HISTORY, "w") as f:
        json.dump(history, f, indent=2)

    # Invalidate cache so next call picks up new rates
    global _learned_rates_cache
    _learned_rates_cache = None

    return count


def project_value(current_value, brand, year, years_ahead, model=None):
    """Compound appreciation from *current_value* over *years_ahead*."""
    if current_value is None or current_value <= 0:
        return None
    rate = appreciation_rate(brand, year, model=model)
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
        "value_1y":  project_value(current, brand, year, 1, model=model),
        "value_2y":  project_value(current, brand, year, 2, model=model),
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
