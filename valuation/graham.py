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
    Returns:
      {
        "model"           : "Graham",
        "iv_simple"       : float or None,
        "iv_adjusted"     : float or None,
        "iv"              : float (best estimate — adjusted if possible),
        "inputs_used"     : dict,
        "note"            : str,
        "valid"           : bool
      }
    """
    eps     = data.get("eps_ttm")
    g_rate  = data.get("eps_growth_5y")   # as decimal e.g. 0.15 = 15%
    y_yield = GSEC_10Y_YIELD              # from config, e.g. 0.07

    # ── Validation ────────────────────────────────────────────────────────
    if not eps or eps <= 0:
        return _invalid("EPS is missing or negative — Graham not applicable")

    if not g_rate or g_rate < 0:
        g_rate = 0.05   # Conservative default if growth unknown
        note = "Growth defaulted to 5% (unavailable)"
    else:
        note = ""

    g_pct = g_rate * 100   # Convert to percentage for formula

    # ── Formula A: Original ────────────────────────────────────────────────
    iv_simple = eps * (GRAHAM_BASE_PE + 2 * g_pct)

    # ── Formula B: Interest Rate Adjusted ─────────────────────────────────
    if y_yield and y_yield > 0:
        iv_adjusted = iv_simple * (GRAHAM_BOND_YIELD_BASE / (y_yield * 100))
    else:
        iv_adjusted = None

    # Best estimate — use adjusted if available
    iv_best = iv_adjusted if iv_adjusted else iv_simple

    # Sanity cap: IV shouldn't be > 50x EPS (extremely high)
    max_iv = eps * 50
    if iv_best > max_iv:
        iv_best = max_iv
        note += " | IV capped at 50x EPS (growth assumption very high)"

    return {
        "model"       : "Graham",
        "iv_simple"   : round(iv_simple, 2),
        "iv_adjusted" : round(iv_adjusted, 2) if iv_adjusted else None,
        "iv"          : round(iv_best, 2),
        "inputs_used" : {
            "eps"       : eps,
            "growth_pct": round(g_pct, 1),
            "gsec_yield": f"{y_yield*100:.1f}%"
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
