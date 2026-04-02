# =============================================================================
# valuation/graham.py — Benjamin Graham Intrinsic Value
#
# Formula A (Original 1962):
#   IV = EPS × (8.5 + 2g)
#
# Formula B (Updated 1974 — Interest Rate Adjusted):
#   IV = EPS × (8.5 + 2g) × (4.4 / Y)
#   Y = Current 10-year G-Sec yield
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GRAHAM_BASE_PE, GRAHAM_BOND_YIELD_BASE, GSEC_10Y_YIELD


def calculate(data: dict) -> dict:
    """
    Implements the Modern Graham Formula:
    IV = [EPS_avg * (7 + 1g) * 4.4] / Y
    Plus a 25% Margin of Safety haircut for institutional conservatism.
    """
    eps_ttm = data.get("eps_ttm")
    g_rate  = data.get("eps_growth_5y")   # as decimal e.g. 0.15 = 15%
    y_yield = GSEC_10Y_YIELD              # from config, e.g. 0.07
    sector  = (data.get("sector") or "").lower()

    # ── 1. Normalized EPS (3-Year Average) ─────────────────────────────────
    # Graham always preached looking at average earnings, not just one year.
    np_series = data.get("net_profit_5y") or []
    shares    = data.get("shares_outstanding")
    
    eps_avg_3y = None
    if shares and shares > 0:
        recent_np = [v for v in np_series[:3] if v is not None]
        if recent_np:
            eps_avg_3y = (sum(recent_np) / len(recent_np)) / shares
            
    # Use the lower of TTM or 3Y Average for conservatism
    eps_to_use = min(eps_ttm, eps_avg_3y) if eps_avg_3y and eps_ttm else eps_ttm

    # ── Validation ────────────────────────────────────────────────────────
    if not eps_to_use or eps_to_use <= 0:
        return _invalid("EPS missing or negative — Graham not applicable")

    if not g_rate or g_rate < 0:
        g_rate = 0.05
        note = "Growth defaulted to 5%"
    else:
        note = ""

    # ── 2. Conservative Growth (Modern Graham) ───────────────────────────
    # The original 2g is too aggressive for today's high interest rates.
    # Modern standard uses 1g and a base PE of 7 or 8.
    g_pct = g_rate * 100
    
    # Sector-aware growth caps (Pharma/IT: 15% | Steel/Energy: 10%)
    g_cap = 15.0
    if "materials" in sector or "steel" in sector or "energy" in sector:
        g_cap = 10.0
    
    g_pct_final = min(g_pct, g_cap)
    if g_pct > g_cap:
        note += f" | Growth capped at {g_cap}% for {sector}"

    # ── 3. Formula Calculation ─────────────────────────────────────────────
    # Modern Formula: IV = EPS * (7 + 1g)
    iv_simple = eps_to_use * (7 + g_pct_final)

    # ── 4. Interest Rate Adjustment & Safety Multiplier ───────────────────
    if y_yield and y_yield > 0:
        # Adjustment = 4.4 / current_bond_yield
        iv_adjusted = iv_simple * (GRAHAM_BOND_YIELD_BASE / (y_yield * 100))
        
        # Apply Institutional Safety Haircut (25%)
        # Graham himself often suggested buying at 2/3rds of IV.
        iv_final = iv_adjusted * 0.75
        note += " | Applied 25% safety haircut"
    else:
        iv_adjusted = None
        iv_final = iv_simple

    return {
        "model"       : "Graham",
        "iv_simple"   : round(iv_simple, 2),
        "iv_adjusted" : round(iv_adjusted, 2) if iv_adjusted else None,
        "iv"          : round(iv_final, 2),
        "inputs_used" : {
            "eps_used"  : round(eps_to_use, 2),
            "growth_pct": round(g_pct_final, 1),
            "gsec_yield": f"{y_yield*100:.1f}%",
            "base_pe"   : 7
        },
        "note"  : note.strip(" |"),
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model"       : "Graham",
        "iv_simple"   : None,
        "iv_adjusted" : None,
        "iv"          : None,
        "inputs_used" : {},
        "note"        : reason,
        "valid"       : False
    }
