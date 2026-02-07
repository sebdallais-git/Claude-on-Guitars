#!/usr/bin/env python3
"""
ml_features — extracts a 19-feature numeric vector from a guitar listing.

Reuses scoring functions from scorer.py and valuation.py to build features
for the ML models (price prediction, buy/skip classification, etc.).

Each feature is derived from listing data, knowledge base, and collection state.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from valuation import _parse_year, _brand_tier, read_collection
from scorer import (
    _score_condition, _match_iconic_model, _score_iconic,
)

# Canonical feature ordering — models depend on this exact sequence
FEATURE_ORDER = [
    "year_numeric",        #  0
    "age",                 #  1
    "price",               #  2
    "reverb_lo",           #  3
    "reverb_hi",           #  4
    "reverb_mid",          #  5
    "reverb_spread",       #  6
    "price_vs_reverb_mid", #  7
    "price_vs_reverb_lo",  #  8
    "brand_tier",          #  9
    "condition_score",     # 10
    "is_golden_era",       # 11
    "iconic_boost",        # 12
    "guitarist_score",     # 13
    "type_electric",       # 14
    "type_acoustic",       # 15
    "type_bass",           # 16
    "era_bucket",          # 17
    "collection_has_brand", # 18
]

# Features used by the price predictor (excludes price-derived to avoid leakage)
PRICE_FEATURES = [f for f in FEATURE_ORDER
                  if f not in ("price", "price_vs_reverb_mid", "price_vs_reverb_lo")]

# Features used by the appreciation predictor (structural only)
APPRECIATION_FEATURES = [
    "year_numeric", "age", "brand_tier", "is_golden_era", "iconic_boost",
    "guitarist_score", "type_electric", "type_acoustic", "type_bass",
    "era_bucket", "condition_score",
]


def _era_bucket(year):
    """Map year to era bucket: 0=pre-1950, 1=1950-65, 2=1965-80, 3=1980-2000, 4=2000+."""
    if year < 1950:
        return 0
    if year < 1965:
        return 1
    if year < 1980:
        return 2
    if year < 2000:
        return 3
    return 4


def _brand_tier_numeric(brand):
    """Return 2=premium, 1=major, 0=minor."""
    tier = _brand_tier(brand)
    return {"premium": 2, "major": 1, "minor": 0}.get(tier, 0)


def extract_features(listing, collection=None):
    """Convert a listing dict into a 19-feature dict.

    Args:
        listing: dict with keys like brand, model, year, price, reverb_lo, etc.
        collection: optional list of owned guitars (for collection_has_brand).

    Returns:
        dict mapping feature name → numeric value.
    """
    brand = listing.get("brand", "")
    model = listing.get("model", "")
    year_raw = listing.get("year", "")
    year = _parse_year(year_raw) or 1970
    price = listing.get("price") or 0.0
    lo = listing.get("reverb_lo") or 0.0
    hi = listing.get("reverb_hi") or 0.0
    mid = (lo + hi) / 2 if (lo and hi) else 0.0
    spread = hi - lo if (lo and hi) else 0.0

    # Price ratios (0 when denominator missing)
    price_vs_mid = (price - mid) / mid if mid > 0 else 0.0
    price_vs_lo = (price - lo) / lo if lo > 0 else 0.0

    # Iconic model info
    iconic = _match_iconic_model(brand, model)
    is_golden = 0
    boost = 0
    if iconic:
        boost = iconic.get("boost", 0)
        era = iconic.get("golden_era")
        if era and era[0] <= year <= era[1]:
            is_golden = 1

    # Guitar type one-hot encoding
    gtype = listing.get("type", "").lower()
    type_electric = 1 if "electric" in gtype else 0
    type_acoustic = 1 if "acoustic" in gtype else 0
    type_bass = 1 if "bass" in gtype else 0

    # Collection brand check
    has_brand = 0
    if collection:
        owned_brands = {g.get("brand", "").lower() for g in collection}
        if brand.lower() in owned_brands:
            has_brand = 1

    return {
        "year_numeric":         float(year),
        "age":                  float(2026 - year),
        "price":                float(price),
        "reverb_lo":            float(lo),
        "reverb_hi":            float(hi),
        "reverb_mid":           float(mid),
        "reverb_spread":        float(spread),
        "price_vs_reverb_mid":  round(price_vs_mid, 4),
        "price_vs_reverb_lo":   round(price_vs_lo, 4),
        "brand_tier":           float(_brand_tier_numeric(brand)),
        "condition_score":      float(_score_condition(listing.get("condition", ""))),
        "is_golden_era":        float(is_golden),
        "iconic_boost":         float(boost),
        "guitarist_score":      float(_score_iconic(brand, model)),
        "type_electric":        float(type_electric),
        "type_acoustic":        float(type_acoustic),
        "type_bass":            float(type_bass),
        "era_bucket":           float(_era_bucket(year)),
        "collection_has_brand": float(has_brand),
    }


def features_to_array(features_dict, feature_list=None):
    """Convert feature dict to ordered list for sklearn.

    Args:
        features_dict: dict from extract_features().
        feature_list: optional custom feature ordering (defaults to FEATURE_ORDER).

    Returns:
        list of floats in canonical order.
    """
    order = feature_list or FEATURE_ORDER
    return [features_dict.get(f, 0.0) for f in order]


if __name__ == "__main__":
    # Quick smoke test
    sample = {
        "brand": "Gibson", "model": "ES-335", "year": "1964",
        "type": "Electric", "price": 12000, "condition": "Excellent",
        "reverb_lo": 8500, "reverb_hi": 14000,
    }
    feats = extract_features(sample)
    print(f"  Features extracted: {len(feats)}")
    for name in FEATURE_ORDER:
        print(f"    {name:25s} = {feats[name]}")
    arr = features_to_array(feats)
    print(f"\n  Array length: {len(arr)}")
