#!/usr/bin/env python3
"""
ml_monitor — daily performance comparison of ML vs rule-based scoring.

Compares ML predictions against actual outcomes (sold prices, etc.) and
tracks metrics over time. Generates auto-recommendations for tuning ml_blend.

Writes results to data/ml/performance.json.

Usage:
    python3 scripts/ml_monitor.py
"""

import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
_DATA         = os.path.join(_PROJECT_ROOT, "data")
_ML_DIR       = os.path.join(_DATA, "ml")
PERFORMANCE_FILE = os.path.join(_ML_DIR, "performance.json")
TRAINING_FILE = os.path.join(_ML_DIR, "training_data.json")
BUDGET_FILE   = os.path.join(_DATA, "budget.json")


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return default if default is not None else {}


def _load_performance():
    return _load_json(PERFORMANCE_FILE, {"daily_logs": []})


def _save_performance(data):
    os.makedirs(_ML_DIR, exist_ok=True)
    with open(PERFORMANCE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _compute_price_accuracy(sold_listings):
    """Compare ML predicted price vs rule-based (Reverb mid) vs actual sold price.

    Returns dict with ml_mae_pct, rule_mae_pct, n.
    """
    from ml_predict import is_ml_available, ml_score_listing
    from valuation import read_collection

    if not is_ml_available():
        return None

    collection = read_collection()
    budget = _load_json(BUDGET_FILE, {"weights": {}, "total": 20000, "spent": 0})

    ml_errors = []
    rule_errors = []

    for listing in sold_listings:
        sold_price = listing.get("sold_price")
        if not sold_price or sold_price <= 0:
            continue

        lo = listing.get("reverb_lo")
        hi = listing.get("reverb_hi")

        # Rule-based price estimate = Reverb midpoint
        if lo and hi and lo > 0:
            reverb_mid = (lo + hi) / 2
            rule_error = abs(reverb_mid - sold_price) / sold_price * 100
            rule_errors.append(rule_error)

        # ML predicted price
        rule_scores = {
            "value": 50.0, "appreciation": 50.0, "fit": 50.0,
            "condition": 50.0, "iconic": 50.0,
        }
        ml_result = ml_score_listing(listing, collection, budget, rule_scores)
        if ml_result and ml_result.get("ml_price"):
            ml_error = abs(ml_result["ml_price"] - sold_price) / sold_price * 100
            ml_errors.append(ml_error)

    if not ml_errors and not rule_errors:
        return None

    return {
        "ml_mae_pct": round(sum(ml_errors) / len(ml_errors), 2) if ml_errors else None,
        "rule_mae_pct": round(sum(rule_errors) / len(rule_errors), 2) if rule_errors else None,
        "n": max(len(ml_errors), len(rule_errors)),
    }


def _compute_score_drift(sold_listings):
    """Compute mean difference between ML and rule-based scores.

    Returns dict with mean_diff and std_diff.
    """
    from ml_predict import is_ml_available, ml_score_listing
    from scorer import score_listing
    from valuation import read_collection

    if not is_ml_available():
        return None

    collection = read_collection()
    budget = _load_json(BUDGET_FILE, {"weights": {}, "total": 20000, "spent": 0})

    diffs = []
    for listing in sold_listings[:100]:  # Cap to avoid slowness
        rule_total, breakdown = score_listing(listing, collection, budget)
        ml_result = ml_score_listing(listing, collection, budget, breakdown)

        if ml_result and ml_result.get("ml_total") is not None:
            diffs.append(ml_result["ml_total"] - rule_total)

    if not diffs:
        return None

    mean_diff = sum(diffs) / len(diffs)
    variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
    std_diff = variance ** 0.5

    return {
        "mean_diff": round(mean_diff, 2),
        "std_diff": round(std_diff, 2),
    }


def _compute_buy_skip_accuracy(sold_listings):
    """Evaluate buy/skip predictions against actual outcomes.

    Returns dict with precision, recall, f1, n.
    """
    from ml_predict import is_ml_available, ml_score_listing
    from valuation import read_collection

    if not is_ml_available():
        return None

    collection = read_collection()
    budget = _load_json(BUDGET_FILE, {"weights": {}, "total": 20000, "spent": 0})

    tp = fp = fn = tn = 0

    for listing in sold_listings:
        lp = listing.get("listed_price") or 0
        sp = listing.get("sold_price") or 0
        if lp <= 0:
            continue

        # Actual outcome: good buy if sold >= 95% asking
        actual_buy = 1 if sp / lp >= 0.95 else 0

        rule_scores = {
            "value": 50.0, "appreciation": 50.0, "fit": 50.0,
            "condition": 50.0, "iconic": 50.0,
        }
        ml_result = ml_score_listing(listing, collection, budget, rule_scores)

        if not ml_result or ml_result.get("ml_buy_prob") is None:
            continue

        # Predict buy if probability > 50%
        predicted_buy = 1 if ml_result["ml_buy_prob"] > 50 else 0

        if predicted_buy == 1 and actual_buy == 1:
            tp += 1
        elif predicted_buy == 1 and actual_buy == 0:
            fp += 1
        elif predicted_buy == 0 and actual_buy == 1:
            fn += 1
        else:
            tn += 1

    total = tp + fp + fn + tn
    if total == 0:
        return None

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "n": total,
    }


def _generate_recommendation(perf_data):
    """Generate auto-recommendation based on performance history."""
    logs = perf_data.get("daily_logs", [])
    if not logs:
        return "No performance data yet. Collect more training data."

    training_data = _load_json(TRAINING_FILE, {"sold_listings": []})
    total_samples = len(training_data.get("sold_listings", []))

    if total_samples < 50:
        return f"Collecting data ({total_samples} samples). ML not yet reliable."

    # Check recent ML vs rule price accuracy
    recent = logs[-7:]  # last 7 days
    ml_better = 0
    rule_better = 0
    for log in recent:
        price = log.get("price_prediction")
        if price and price.get("ml_mae_pct") is not None and price.get("rule_mae_pct") is not None:
            if price["ml_mae_pct"] < price["rule_mae_pct"]:
                ml_better += 1
            else:
                rule_better += 1

    if ml_better >= 5:
        return "ML outperforming rules for 5+ days. Consider increasing ml_blend."
    if rule_better >= 3:
        return "ML underperforming rules. Consider reducing ml_blend or retraining."

    return "Performance tracking in progress. More data needed for recommendation."


def run_monitor():
    """Run daily monitoring comparison."""
    print("  ML Performance Monitor")
    print("  " + "=" * 40)

    from ml_predict import is_ml_available, get_model_status, active_model_count

    if not is_ml_available():
        print("  No ML models available. Train models first (python3 scripts/ml_train.py)")
        return

    status = get_model_status()
    models_active = [name for name, info in status.items() if info["available"]]
    print(f"  Active models: {len(models_active)}/4 ({', '.join(models_active)})")

    # Load sold data for evaluation
    training_data = _load_json(TRAINING_FILE, {"sold_listings": []})
    sold = training_data.get("sold_listings", [])
    print(f"  Evaluation data: {len(sold)} sold listings")

    if not sold:
        print("  No sold data for evaluation. Run reverb_sold.py first.")
        return

    # Compute metrics
    print("\n  Computing metrics...")

    price_acc = _compute_price_accuracy(sold)
    if price_acc:
        ml_str = f"{price_acc['ml_mae_pct']:.1f}%" if price_acc["ml_mae_pct"] is not None else "N/A"
        rule_str = f"{price_acc['rule_mae_pct']:.1f}%" if price_acc["rule_mae_pct"] is not None else "N/A"
        print(f"    Price MAE:    ML={ml_str}  Rule={rule_str}  (n={price_acc['n']})")

    drift = _compute_score_drift(sold)
    if drift:
        print(f"    Score drift:  mean={drift['mean_diff']:+.1f}  std={drift['std_diff']:.1f}")

    buy_skip = _compute_buy_skip_accuracy(sold)
    if buy_skip:
        print(f"    Buy/skip:     P={buy_skip['precision']:.2f}  R={buy_skip['recall']:.2f}  "
              f"F1={buy_skip['f1']:.2f}  (n={buy_skip['n']})")

    # Build daily log entry
    today = date.today().isoformat()
    perf_data = _load_performance()

    # Remove existing entry for today (idempotent reruns)
    perf_data["daily_logs"] = [
        log for log in perf_data.get("daily_logs", [])
        if log.get("date") != today
    ]

    log_entry = {
        "date": today,
        "models_active": models_active,
        "training_samples": len(sold),
        "price_prediction": price_acc,
        "score_drift": drift,
        "buy_skip": buy_skip,
    }

    perf_data["daily_logs"].append(log_entry)

    # Keep last 90 days
    perf_data["daily_logs"] = perf_data["daily_logs"][-90:]

    # Generate recommendation
    recommendation = _generate_recommendation(perf_data)
    log_entry["recommendation"] = recommendation

    _save_performance(perf_data)

    print(f"\n  Recommendation: {recommendation}")
    print(f"  Performance log saved to {PERFORMANCE_FILE}")


if __name__ == "__main__":
    run_monitor()
