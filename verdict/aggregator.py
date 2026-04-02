# =============================================================================
# verdict/aggregator.py — Weighted Intrinsic Value Aggregator
#
# Takes results from all valuation models + detection type,
# computes a weighted average IV using stock-type-aware weights.
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from screening.detector import (
    BANK_NBFC, PSU, EARLY_STAGE, CYCLICAL,
    HIGH_GROWTH, LARGE_STABLE, GENERAL, REIT
)


def aggregate(results: dict, detection: dict) -> dict:
    """
    results   : dict of {model_name: model_result_dict}
    detection : output from detector.detect()

    Returns:
      {
        "weighted_iv"     : float or None,
        "model_ivs"       : dict {model: iv},
        "weights_used"    : dict {model: weight},
        "iv_range"        : tuple (low, high),
        "confidence"      : str,
        "note"            : str
      }
    """
    stock_type = detection.get("stock_type", GENERAL)
    weights    = detection.get("weights", {})

    # ── Collect valid IVs from each model ─────────────────────────────────
    model_ivs = {}
    for model_name, result in results.items():
        if result and result.get("valid") and result.get("iv") is not None:
            iv = result["iv"]
            if iv > 0:
                model_ivs[model_name] = iv

    if not model_ivs:
        return {
            "weighted_iv" : None,
            "model_ivs"   : {},
            "weights_used": {},
            "iv_range"    : (None, None),
            "confidence"  : "NO DATA",
            "note"        : "No valid intrinsic values computed"
        }

    # ── Map model names to weight keys ────────────────────────────────────
    # Model result keys → weight dict keys
    MODEL_TO_WEIGHT_KEY = {
        "Graham"       : "graham",
        "DCF"          : "dcf",
        "Lynch"        : "lynch",
        "Buffett"      : "buffett",
        "EPV"          : "epv",
        "DDM"          : "ddm",
        "ExcessReturns": "excess_returns",
        "EV/Sales"     : "ev_sales",
        "MidCycleEV"   : "mid_cycle",
        # New models
        "NAV"          : "nav",
        "PriceTAM"     : "price_tam",
    }

    # ── REIT-specific: if NAV model available, it dominates ──────────────
    if stock_type == REIT:
        if "NAV" in model_ivs and model_ivs["NAV"] > 0:
            # Ensure NAV gets 70% weight, DDM gets remaining share
            weights = {k: v for k, v in weights.items()}
            weights["nav"] = 0.70
            weights["ddm"] = 0.30

    # ── EARLY_STAGE: if PriceTAM available, blend with EV/Sales ─────────
    if stock_type == EARLY_STAGE:
        if "PriceTAM" in model_ivs and "EV/Sales" in model_ivs:
            weights = {"ev_sales": 0.45, "price_tam": 0.35, "relative": 0.20}
        elif "PriceTAM" in model_ivs:
            weights = {"price_tam": 0.70, "relative": 0.30}
        elif "EV/Sales" in model_ivs:
            weights = {"ev_sales": 0.70, "relative": 0.30}

    # ── Apply weights ──────────────────────────────────────────────────────
    weighted_sum  = 0.0
    total_weight  = 0.0
    weights_used  = {}

    for model_name, iv in model_ivs.items():
        wkey   = MODEL_TO_WEIGHT_KEY.get(model_name, model_name.lower())
        weight = weights.get(wkey, 0)

        # If a valid model has no explicit weight, give equal share of remainder
        if weight == 0 and wkey not in weights:
            weight = 0.15   # Fallback contribution

        weighted_sum += iv * weight
        total_weight += weight
        weights_used[model_name] = weight

    if total_weight == 0:
        # Equal weight fallback
        n = len(model_ivs)
        weighted_iv = sum(model_ivs.values()) / n
        weights_used = {m: round(1/n, 2) for m in model_ivs}
    else:
        weighted_iv = weighted_sum / total_weight

    # ── IV Range (min/max of valid models) ────────────────────────────────
    iv_vals  = list(model_ivs.values())
    iv_range = (round(min(iv_vals), 2), round(max(iv_vals), 2))

    # ── Confidence based on number of valid models ────────────────────────
    n = len(model_ivs)
    if n >= 3:
        confidence = "HIGH"
    elif n == 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW — only 1 model available"

    # ── Spread check: if models diverge too much, flag it ─────────────────
    spread_pct = (iv_range[1] - iv_range[0]) / weighted_iv * 100 if weighted_iv > 0 else 0
    note_parts = [f"Weighted IV from {n} model(s)"]
    if spread_pct > 50:
        note_parts.append(
            f"⚠ High model divergence ({spread_pct:.0f}%) — "
            "check growth assumptions carefully"
        )

    return {
        "weighted_iv" : round(weighted_iv, 2),
        "model_ivs"   : {k: round(v, 2) for k, v in model_ivs.items()},
        "model_results": results,  # Pass through full results for decision gate
        "weights_used": {k: round(v, 3) for k, v in weights_used.items()},
        "iv_range"    : iv_range,
        "confidence"  : confidence,
        "note"        : " | ".join(note_parts)
    }
