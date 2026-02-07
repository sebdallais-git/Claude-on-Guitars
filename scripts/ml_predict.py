#!/usr/bin/env python3
"""
ml_predict — inference module for the hybrid ML scoring system.

Lazy-loads trained models from data/ml/models/ and provides scoring functions.
Gracefully returns None when models are unavailable (cold start).

The hybrid blending formula:
    final_score = (1 - ml_blend) * rule_total + ml_blend * ml_total

Usage:
    from ml_predict import is_ml_available, ml_score_listing
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA         = os.path.join(_PROJECT_ROOT, "data")
_ML_DIR       = os.path.join(_DATA, "ml")
_MODELS_DIR   = os.path.join(_ML_DIR, "models")

# Lazy-loaded model cache
_model_cache = {}
_meta_cache = {}
_load_attempted = False

MODEL_NAMES = [
    "weight_optimizer",
    "price_predictor",
    "appreciation_predictor",
    "buy_classifier",
]


def _ensure_loaded():
    """Attempt to load all available models once."""
    global _load_attempted
    if _load_attempted:
        return
    _load_attempted = True

    try:
        import joblib
    except ImportError:
        return

    for name in MODEL_NAMES:
        model_path = os.path.join(_MODELS_DIR, f"{name}.joblib")
        meta_path = os.path.join(_MODELS_DIR, f"{name}_meta.json")

        if os.path.exists(model_path):
            try:
                _model_cache[name] = joblib.load(model_path)
            except Exception:
                pass

        if os.path.exists(meta_path):
            try:
                with open(meta_path) as f:
                    _meta_cache[name] = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass


def is_ml_available():
    """True if at least one model is trained and loadable."""
    _ensure_loaded()
    return len(_model_cache) > 0


def get_model_status():
    """Return dict of model name → {available, trained_at, samples, metrics}."""
    _ensure_loaded()
    status = {}
    for name in MODEL_NAMES:
        meta = _meta_cache.get(name, {})
        status[name] = {
            "available": name in _model_cache,
            "trained_at": meta.get("trained_at"),
            "samples": meta.get("samples", 0),
            "metrics": meta.get("metrics", {}),
        }
    return status


def get_learned_weights():
    """Return learned dimension weights if weight_optimizer is available."""
    _ensure_loaded()
    meta = _meta_cache.get("weight_optimizer", {})
    return meta.get("learned_weights")


def ml_score_listing(entry, collection, budget, rule_scores):
    """Score a listing using available ML models.

    Args:
        entry: listing dict (same as scorer.py uses).
        collection: list of owned guitars.
        budget: budget dict from budget.json.
        rule_scores: dict with rule-based sub-scores
            {"value": float, "appreciation": float, "fit": float,
             "condition": float, "iconic": float}.

    Returns:
        dict with ML results, or None if no models available:
        {
            "ml_total":          float or None,  # ML composite score
            "ml_weights":        dict or None,   # learned weights used
            "ml_price":          float or None,  # predicted price
            "ml_appreciation":   float or None,  # predicted appreciation %
            "ml_buy_prob":       float or None,  # buy probability 0-100
            "rule_total":        float,           # original rule score
        }
    """
    _ensure_loaded()

    if not _model_cache:
        return None

    from ml_features import (
        extract_features, features_to_array,
        FEATURE_ORDER, PRICE_FEATURES, APPRECIATION_FEATURES,
    )

    feats = extract_features(entry, collection)
    result = {
        "ml_total": None,
        "ml_weights": None,
        "ml_price": None,
        "ml_appreciation": None,
        "ml_buy_prob": None,
    }

    # Weight optimizer: compute ML total from rule sub-scores using learned weights
    if "weight_optimizer" in _model_cache:
        learned_w = get_learned_weights()
        if learned_w:
            ml_total = (
                learned_w.get("value", 0.2) * rule_scores["value"]
                + learned_w.get("appreciate", 0.2) * rule_scores["appreciation"]
                + learned_w.get("fit", 0.2) * rule_scores["fit"]
                + learned_w.get("condition", 0.2) * rule_scores["condition"]
                + learned_w.get("iconic", 0.2) * rule_scores["iconic"]
            )
            result["ml_total"] = round(ml_total, 1)
            result["ml_weights"] = learned_w

    # Price predictor
    if "price_predictor" in _model_cache:
        try:
            arr = features_to_array(feats, PRICE_FEATURES)
            predicted = _model_cache["price_predictor"].predict([arr])[0]
            result["ml_price"] = round(max(0, predicted), 2)
        except Exception:
            pass

    # Appreciation predictor
    if "appreciation_predictor" in _model_cache:
        try:
            arr = features_to_array(feats, APPRECIATION_FEATURES)
            predicted = _model_cache["appreciation_predictor"].predict([arr])[0]
            result["ml_appreciation"] = round(predicted, 2)  # percentage
        except Exception:
            pass

    # Buy/skip classifier
    if "buy_classifier" in _model_cache:
        try:
            arr = features_to_array(feats, FEATURE_ORDER)
            prob = _model_cache["buy_classifier"].predict_proba([arr])[0]
            # prob[1] = probability of class 1 (buy)
            buy_prob = prob[1] if len(prob) > 1 else prob[0]
            result["ml_buy_prob"] = round(buy_prob * 100, 1)
        except Exception:
            pass

    return result


def active_model_count():
    """Return count of loaded models."""
    _ensure_loaded()
    return len(_model_cache)


def total_training_samples():
    """Return total training samples across all models."""
    _ensure_loaded()
    return sum(m.get("samples", 0) for m in _meta_cache.values())


if __name__ == "__main__":
    _ensure_loaded()
    print(f"  ML models available: {is_ml_available()}")
    print(f"  Models loaded: {active_model_count()}/4")
    status = get_model_status()
    for name, info in status.items():
        avail = "ready" if info["available"] else "not trained"
        print(f"    {name}: {avail} ({info['samples']} samples)")
