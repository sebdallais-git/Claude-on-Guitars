#!/usr/bin/env python3
"""
ml_train — trains 4 ML models for the hybrid scoring system.

Models:
  1. Weight Optimizer   — learns optimal dimension weights from sold data
  2. Price Predictor    — predicts sold price from guitar features
  3. Appreciation       — predicts annual appreciation rate per model
  4. Buy/Skip Classifier — buy probability from all features

Requires scikit-learn and joblib. All models are saved under data/ml/models/.
Each model also produces a *_meta.json with training metrics.

Usage:
    python3 scripts/ml_train.py
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA         = os.path.join(_PROJECT_ROOT, "data")
_ML_DIR       = os.path.join(_DATA, "ml")
_MODELS_DIR   = os.path.join(_ML_DIR, "models")
TRAINING_FILE = os.path.join(_ML_DIR, "training_data.json")
BUDGET_FILE   = os.path.join(_DATA, "budget.json")
COLLECTION_FILE = os.path.join(_DATA, "collection.json")
PRICE_HISTORY = os.path.join(_DATA, "price_history.json")

# Minimum data thresholds per model
MIN_WEIGHT_OPT  = 30
MIN_PRICE_PRED  = 50
MIN_APPRECIATION = 20
MIN_BUY_SKIP    = 30
MIN_PER_CLASS   = 10


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return default if default is not None else {}


def _save_meta(model_name, meta):
    """Save model metadata JSON."""
    os.makedirs(_MODELS_DIR, exist_ok=True)
    path = os.path.join(_MODELS_DIR, f"{model_name}_meta.json")
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)


def _load_training_data():
    """Load sold listings from training_data.json."""
    data = _load_json(TRAINING_FILE, {"sold_listings": [], "user_decisions": []})
    return data.get("sold_listings", []), data.get("user_decisions", [])


def train_weight_optimizer(sold_listings, budget):
    """Model 1: Learn optimal dimension weights from sold data.

    Uses Ridge regression to find weights that best predict desirability
    (sold_price / listed_price ratio) from the 5 rule-based sub-scores.
    """
    print("\n  [1/4] Weight Optimizer")

    # Filter listings with valid prices
    valid = [s for s in sold_listings
             if s.get("listed_price") and s.get("sold_price")
             and s["listed_price"] > 0]

    if len(valid) < MIN_WEIGHT_OPT:
        print(f"    Skipped: {len(valid)} samples < {MIN_WEIGHT_OPT} minimum")
        return False

    from sklearn.linear_model import Ridge
    import joblib

    from ml_features import extract_features
    from scorer import (
        _score_value, _score_appreciation, _score_fit,
        _score_condition, _score_iconic,
    )
    from valuation import read_collection

    collection = read_collection()

    X = []
    y = []

    for listing in valid:
        # Compute the 5 rule-based sub-scores
        s_val = _score_value(
            listing.get("listed_price"),
            listing.get("reverb_lo"),
            listing.get("reverb_hi"),
        )
        s_app = _score_appreciation(
            listing.get("brand", ""),
            listing.get("year", ""),
            model=listing.get("model"),
        )
        s_fit = _score_fit(listing, collection)
        s_cond = _score_condition(listing.get("condition", ""))
        s_icon = _score_iconic(listing.get("brand", ""), listing.get("model", ""))

        X.append([s_val, s_app, s_fit, s_cond, s_icon])

        # Target: desirability = sold/listed ratio, capped at 1.0, scaled to 100
        desirability = min(1.0, listing["sold_price"] / listing["listed_price"]) * 100
        y.append(desirability)

    model = Ridge(alpha=1.0)
    model.fit(X, y)

    # Extract and normalize weights (clip negatives, normalize to sum=1)
    raw_weights = model.coef_
    clipped = [max(0, w) for w in raw_weights]
    total = sum(clipped)
    if total > 0:
        learned_weights = [round(w / total, 4) for w in clipped]
    else:
        learned_weights = [0.2] * 5

    weight_names = ["value", "appreciate", "fit", "condition", "iconic"]
    weight_dict = dict(zip(weight_names, learned_weights))

    # Save model
    os.makedirs(_MODELS_DIR, exist_ok=True)
    model_path = os.path.join(_MODELS_DIR, "weight_optimizer.joblib")
    joblib.dump(model, model_path)

    # Save metadata
    from sklearn.metrics import r2_score, mean_absolute_error
    preds = model.predict(X)
    _save_meta("weight_optimizer", {
        "trained_at": datetime.now().isoformat(),
        "samples": len(X),
        "metrics": {
            "r2": round(r2_score(y, preds), 4),
            "mae": round(mean_absolute_error(y, preds), 2),
        },
        "learned_weights": weight_dict,
        "feature_importances": weight_dict,
        "version": 1,
    })

    print(f"    Trained on {len(X)} samples")
    print(f"    Learned weights: {weight_dict}")
    print(f"    R2: {r2_score(y, preds):.4f}")
    return True


def train_price_predictor(sold_listings):
    """Model 2: Predict sold price from guitar features.

    Uses GradientBoosting on 15 features (excludes price-derived to avoid leakage).
    """
    print("\n  [2/4] Price Predictor")

    valid = [s for s in sold_listings
             if s.get("sold_price") and s["sold_price"] > 0]

    if len(valid) < MIN_PRICE_PRED:
        print(f"    Skipped: {len(valid)} samples < {MIN_PRICE_PRED} minimum")
        return False

    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib

    from ml_features import extract_features, features_to_array, PRICE_FEATURES
    from valuation import read_collection

    collection = read_collection()

    X = []
    y = []

    for listing in valid:
        feats = extract_features(listing, collection)
        arr = features_to_array(feats, PRICE_FEATURES)
        X.append(arr)
        y.append(listing["sold_price"])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    # MAE as percentage of actual price
    mae_pct = (mae / (sum(y_test) / len(y_test))) * 100 if y_test else 0

    # Feature importances
    importances = dict(zip(PRICE_FEATURES, [round(v, 4) for v in model.feature_importances_]))

    os.makedirs(_MODELS_DIR, exist_ok=True)
    model_path = os.path.join(_MODELS_DIR, "price_predictor.joblib")
    joblib.dump(model, model_path)

    _save_meta("price_predictor", {
        "trained_at": datetime.now().isoformat(),
        "samples": len(X),
        "test_samples": len(X_test),
        "metrics": {
            "mae": round(mae, 2),
            "mae_pct": round(mae_pct, 2),
            "r2": round(r2_score(y_test, preds), 4),
        },
        "feature_importances": importances,
        "version": 1,
    })

    print(f"    Trained on {len(X_train)} / tested on {len(X_test)} samples")
    print(f"    MAE: ${mae:,.0f} ({mae_pct:.1f}%)")
    print(f"    R2:  {r2_score(y_test, preds):.4f}")
    return True


def train_appreciation_predictor():
    """Model 3: Predict annual appreciation rate from guitar features.

    Uses RandomForest on structural features. Training data comes from
    learned rates in price_history.json.
    """
    print("\n  [3/4] Appreciation Predictor")

    history = _load_json(PRICE_HISTORY, {"learned_rates": {}})
    learned = history.get("learned_rates", {})

    if len(learned) < MIN_APPRECIATION:
        print(f"    Skipped: {len(learned)} models with rates < {MIN_APPRECIATION} minimum")
        return False

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib

    from ml_features import extract_features, features_to_array, APPRECIATION_FEATURES

    X = []
    y = []

    for key, rate in learned.items():
        parts = key.split("|", 1)
        if len(parts) != 2:
            continue
        brand, model = parts

        # Create a minimal listing for feature extraction
        listing = {"brand": brand, "model": model, "year": "", "type": "Electric"}
        feats = extract_features(listing)
        arr = features_to_array(feats, APPRECIATION_FEATURES)
        X.append(arr)
        y.append(rate * 100)  # Convert to percentage for easier interpretation

    model = RandomForestRegressor(
        n_estimators=100, max_depth=6, random_state=42
    )
    model.fit(X, y)

    preds = model.predict(X)
    mae = mean_absolute_error(y, preds)

    importances = dict(zip(
        APPRECIATION_FEATURES,
        [round(v, 4) for v in model.feature_importances_]
    ))

    os.makedirs(_MODELS_DIR, exist_ok=True)
    model_path = os.path.join(_MODELS_DIR, "appreciation_predictor.joblib")
    joblib.dump(model, model_path)

    _save_meta("appreciation_predictor", {
        "trained_at": datetime.now().isoformat(),
        "samples": len(X),
        "metrics": {
            "mae_pct_points": round(mae, 2),
            "r2": round(r2_score(y, preds), 4),
        },
        "feature_importances": importances,
        "version": 1,
    })

    print(f"    Trained on {len(X)} models with learned rates")
    print(f"    MAE: {mae:.2f} percentage points")
    return True


def train_buy_classifier(sold_listings, user_decisions):
    """Model 4: Buy/skip binary classifier.

    Buy (1): guitars in user's collection + sold at >= 95% asking price.
    Skip (0): not sold / low desirability.
    """
    print("\n  [4/4] Buy/Skip Classifier")

    from valuation import read_collection
    collection = read_collection()

    # Build labeled dataset
    positives = []  # buy
    negatives = []  # skip

    # User collection = positive examples
    for g in collection:
        if g.get("brand") and g.get("model"):
            positives.append(g)

    # Sold at >= 95% asking = positive; rest = negative
    for listing in sold_listings:
        lp = listing.get("listed_price") or 0
        sp = listing.get("sold_price") or 0
        if lp > 0 and sp > 0:
            if sp / lp >= 0.95:
                positives.append(listing)
            else:
                negatives.append(listing)

    # Include explicit user decisions if available
    for decision in user_decisions:
        if decision.get("action") == "buy":
            positives.append(decision)
        elif decision.get("action") == "skip":
            negatives.append(decision)

    total = len(positives) + len(negatives)
    if total < MIN_BUY_SKIP or len(positives) < MIN_PER_CLASS or len(negatives) < MIN_PER_CLASS:
        print(f"    Skipped: {len(positives)} buy + {len(negatives)} skip "
              f"(need {MIN_BUY_SKIP} total, {MIN_PER_CLASS} per class)")
        return False

    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, f1_score
    import joblib

    from ml_features import extract_features, features_to_array, FEATURE_ORDER

    X = []
    y = []

    for item in positives:
        feats = extract_features(item, collection)
        X.append(features_to_array(feats))
        y.append(1)

    for item in negatives:
        feats = extract_features(item, collection)
        X.append(features_to_array(feats))
        y.append(0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=100, max_depth=4, random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)

    importances = dict(zip(
        FEATURE_ORDER,
        [round(v, 4) for v in model.feature_importances_]
    ))

    os.makedirs(_MODELS_DIR, exist_ok=True)
    model_path = os.path.join(_MODELS_DIR, "buy_classifier.joblib")
    joblib.dump(model, model_path)

    _save_meta("buy_classifier", {
        "trained_at": datetime.now().isoformat(),
        "samples": len(X),
        "test_samples": len(X_test),
        "class_balance": {"buy": len(positives), "skip": len(negatives)},
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        "feature_importances": importances,
        "version": 1,
    })

    print(f"    Trained on {len(X_train)} / tested on {len(X_test)} samples")
    print(f"    Balance: {len(positives)} buy / {len(negatives)} skip")
    print(f"    Precision: {precision:.2f}  Recall: {recall:.2f}  F1: {f1:.2f}")
    return True


def train_all():
    """Train all 4 models. Each checks its own data threshold."""
    print("  ML Model Training")
    print("  " + "=" * 40)

    try:
        import sklearn  # noqa: F401
        import joblib    # noqa: F401
    except ImportError:
        print("  scikit-learn or joblib not installed.")
        print("  Install with: pip install scikit-learn joblib")
        return

    sold_listings, user_decisions = _load_training_data()
    budget = _load_json(BUDGET_FILE, {"weights": {}})

    print(f"  Training data:  {len(sold_listings)} sold listings")
    print(f"  User decisions: {len(user_decisions)} decisions")

    results = {}
    results["weight_optimizer"] = train_weight_optimizer(sold_listings, budget)
    results["price_predictor"] = train_price_predictor(sold_listings)
    results["appreciation_predictor"] = train_appreciation_predictor()
    results["buy_classifier"] = train_buy_classifier(sold_listings, user_decisions)

    trained = sum(1 for v in results.values() if v)
    print(f"\n  Training complete: {trained}/4 models trained")
    for name, ok in results.items():
        status = "trained" if ok else "skipped (insufficient data)"
        print(f"    {name}: {status}")


if __name__ == "__main__":
    train_all()
