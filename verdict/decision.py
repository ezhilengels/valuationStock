# =============================================================================
# verdict/decision.py — Final BUY / HOLD / OVERVALUED Decision Engine
#
# Step 1: Margin of safety vs weighted IV
# Step 2: Quality gate override
# Step 3: Relative valuation gate
# Step 4: Special flags (cyclical peak, early-stage warning)
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    STRONG_BUY_THRESHOLD, BUY_THRESHOLD,
    HOLD_UPPER, OVERVALUED_THRESHOLD
)
from screening.detector import EARLY_STAGE, CYCLICAL


# Verdict constants
STRONG_BUY  = "STRONG BUY"
BUY         = "BUY"
HOLD        = "HOLD"
OVERVALUED  = "OVERVALUED"
AVOID       = "AVOID"
EARLY_STAGE_FLAG = "EARLY STAGE — SPECULATIVE"


def decide(cmp: float, agg: dict, quality: dict,
           relative: dict, detection: dict) -> dict:
    """
    cmp       : Current Market Price
    agg       : aggregator.aggregate() output
    quality   : quality_filter.run() output
    relative  : relative.calculate() output
    detection : detector.detect() output

    Returns:
      {
        "verdict"       : str,
        "verdict_color" : str,   # for terminal display
        "discount_pct"  : float, # discount (positive) or premium (negative) to IV
        "weighted_iv"   : float,
        "margin_verdict": str,
        "quality_grade" : str,
        "relative_grade": str,
        "flags"         : list,
        "rationale"     : str,
        "action"        : str    # specific suggested action
      }
    """
    weighted_iv  = agg.get("weighted_iv")
    stock_type   = detection.get("stock_type", "GENERAL")
    quality_grade= quality.get("grade", "N/A")
    quality_score= quality.get("score", 0)
    rel_overall  = (relative or {}).get("overall_relative", "N/A")
    flags        = []

    # ── No IV computed ────────────────────────────────────────────────────
    if not weighted_iv or not cmp:
        return _result(
            verdict    = AVOID,
            color      = "RED",
            discount   = None,
            iv         = weighted_iv,
            margin_v   = "Cannot compute",
            q_grade    = quality_grade,
            rel_grade  = rel_overall,
            flags      = ["Insufficient data to compute intrinsic value"],
            rationale  = "No intrinsic value could be calculated",
            action     = "Gather more financial data before investing"
        )

    # ── Bond First Gate: Earnings Yield vs G-Sec ──────────────────────────
    # If risk-free bonds pay more than the stock's earnings yield, avoid.
    buffett_res = agg.get("model_results", {}).get("Buffett", {})
    ey          = buffett_res.get("earnings_yield")
    gsec        = buffett_res.get("gsec_yield")
    ey_fail     = False
    
    if ey and gsec and ey < gsec:
        ey_fail = True
        flags.append(f"⚠ BOND GATE FAILED: G-Sec ({gsec:.1f}%) > Stock Yield ({ey:.1f}%)")
        flags.append("Risk-free bonds offer better returns than this stock.")
    if stock_type == EARLY_STAGE:
        flags.append("⚠ Loss-making / pre-profit company — EV/Sales used")
        flags.append("High risk: valuation is speculative, not intrinsic")
        return _result(
            verdict    = EARLY_STAGE_FLAG,
            color      = "YELLOW",
            discount   = _discount(cmp, weighted_iv),
            iv         = weighted_iv,
            margin_v   = "Not applicable — EV/Sales comparison",
            q_grade    = quality_grade,
            rel_grade  = rel_overall,
            flags      = flags,
            rationale  = "Earnings-based valuation not applicable. EV/Sales peer comparison used.",
            action     = "Only invest if you have high risk tolerance and long (5Y+) horizon"
        )

    # ── Discount / Premium Calculation ────────────────────────────────────
    discount = _discount(cmp, weighted_iv)
    # Positive = stock is BELOW IV (discount, good)
    # Negative = stock is ABOVE IV (premium, risky)

    # ── Margin of Safety Verdict ──────────────────────────────────────────
    if discount >= STRONG_BUY_THRESHOLD:
        margin_verdict = f"DEEP DISCOUNT ({discount*100:.1f}% below IV)"
        raw_verdict    = STRONG_BUY
    elif discount >= BUY_THRESHOLD:
        margin_verdict = f"DISCOUNT ({discount*100:.1f}% below IV)"
        raw_verdict    = BUY
    elif discount >= HOLD_UPPER:
        margin_verdict = f"FAIRLY VALUED ({discount*100:.1f}% below IV)"
        raw_verdict    = HOLD
    elif discount >= -OVERVALUED_THRESHOLD:
        margin_verdict = f"SLIGHTLY PREMIUM ({abs(discount)*100:.1f}% above IV)"
        raw_verdict    = OVERVALUED
    else:
        margin_verdict = f"SIGNIFICANTLY OVERPRICED ({abs(discount)*100:.1f}% above IV)"
        raw_verdict    = AVOID

    # ── Bond Gate Override ────────────────────────────────────────────────
    if ey_fail and raw_verdict in [STRONG_BUY, BUY]:
        raw_verdict = HOLD
        flags.append("Verdict downgraded to HOLD because risk-free bonds are currently more attractive")
    elif ey_fail and raw_verdict == HOLD:
        raw_verdict = OVERVALUED
        flags.append("Verdict downgraded to OVERVALUED because bond yield > earnings yield")

    # ── Quality Gate Override ─────────────────────────────────────────────
    if quality_grade == "FAIL":
        flags.append(f"⚠ QUALITY GATE FAILED (score {quality_score}/100) — "
                     f"Failed: {', '.join(quality.get('failed', []))}")
        if raw_verdict in [STRONG_BUY, BUY]:
            raw_verdict = HOLD
            flags.append("Verdict downgraded to HOLD due to quality concerns")

    # ── Relative Valuation Gate ───────────────────────────────────────────
    if rel_overall == "CHEAP vs PEERS" and raw_verdict in [STRONG_BUY, BUY]:
        flags.append("✓ Cheap vs sector peers — supports buy case")
    elif rel_overall == "EXPENSIVE vs PEERS" and raw_verdict == OVERVALUED:
        raw_verdict = AVOID
        flags.append("⚠ Expensive vs sector peers AND overvalued — upgraded to AVOID")
    elif rel_overall == "EXPENSIVE vs PEERS" and raw_verdict in [STRONG_BUY, BUY]:
        flags.append("⚠ Note: Expensive vs peers despite IV discount — verify growth assumptions")

    # ── Cyclical Peak Warning ─────────────────────────────────────────────
    if stock_type == CYCLICAL:
        flags.append("⚠ CYCLICAL: Using mid-cycle EBITDA. Current P/E is meaningless.")

    # ── Confidence Flag ───────────────────────────────────────────────────
    confidence = agg.get("confidence", "")
    if "LOW" in confidence:
        flags.append(f"⚠ Low confidence: {confidence} — treat IV as approximate")

    # ── Color Coding ──────────────────────────────────────────────────────
    colors = {
        STRONG_BUY      : "GREEN",
        BUY             : "GREEN",
        HOLD            : "YELLOW",
        OVERVALUED      : "RED",
        AVOID           : "RED",
        EARLY_STAGE_FLAG: "YELLOW"
    }

    # ── Action Text ───────────────────────────────────────────────────────
    actions = {
        STRONG_BUY : "Consider accumulating — 30%+ margin of safety present",
        BUY        : "Attractive entry point — 15-30% margin of safety",
        HOLD       : "Hold existing position — wait for better price",
        OVERVALUED : "Avoid fresh buying — stock is priced above intrinsic value",
        AVOID      : "Do not invest — significantly overpriced or quality concerns"
    }

    # ── Rationale ─────────────────────────────────────────────────────────
    rationale = (
        f"Weighted IV: ₹{weighted_iv:,.0f} | CMP: ₹{cmp:,.0f} | "
        f"Margin of Safety: {discount*100:+.1f}% | "
        f"Quality: {quality_grade} ({quality_score}/100) | "
        f"Peers: {rel_overall}"
    )

    return _result(
        verdict    = raw_verdict,
        color      = colors.get(raw_verdict, "WHITE"),
        discount   = discount,
        iv         = weighted_iv,
        margin_v   = margin_verdict,
        q_grade    = quality_grade,
        rel_grade  = rel_overall,
        flags      = flags,
        rationale  = rationale,
        action     = actions.get(raw_verdict, "")
    )


def _discount(cmp: float, iv: float) -> float:
    """Positive = discount to IV. Negative = premium over IV."""
    if iv <= 0:
        return -1.0
    return (iv - cmp) / iv


def _result(verdict, color, discount, iv, margin_v,
            q_grade, rel_grade, flags, rationale, action):
    return {
        "verdict"       : verdict,
        "verdict_color" : color,
        "discount_pct"  : round(discount * 100, 1) if discount is not None else None,
        "weighted_iv"   : iv,
        "margin_verdict": margin_v,
        "quality_grade" : q_grade,
        "relative_grade": rel_grade,
        "flags"         : flags,
        "rationale"     : rationale,
        "action"        : action
    }
