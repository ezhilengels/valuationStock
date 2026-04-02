# =============================================================================
# valuation/ddm.py — Dividend Discount Model (Gordon Growth Model)
#
# IV = D1 / (r − g)
# D1 = Expected next year dividend = DPS × (1 + g)
# r  = Required return (12%)
# g  = Dividend growth rate (5Y CAGR)
#
# Best for: PSUs, FMCG, ITC, Coal India, mature companies
# Skip if: dividend yield < 1% or no consistent dividend history
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_discount_rate, GSEC_10Y_YIELD


def calculate(data: dict) -> dict:
    """
    Returns:
      {
        "model"          : "DDM",
        "iv"             : float or None,
        "d1"             : float,
        "dps"            : float,
        "growth_rate"    : float,
        "required_return": float,
        "dividend_yield" : float,
        "inputs_used"    : dict,
        "note"           : str,
        "valid"          : bool
      }
    """
    dps       = data.get("dps") or 0
    g_rate    = data.get("dps_growth_5y") or 0.05
    cmp       = data.get("cmp")
    beta      = data.get("beta") or 1.0
    r         = get_discount_rate(beta)

    # ── Validation ─────────────────────────────────────────────────────────
    if not dps or dps <= 0:
        return _invalid(
            "No dividend paid — DDM not applicable. "
            "Use DCF or Owner Earnings instead."
        )

    # Dividend yield check
    div_yield = (dps / cmp * 100) if cmp and cmp > 0 else 0
    if div_yield < 0.5:
        return _invalid(
            f"Dividend yield too low ({div_yield:.2f}%) — DDM unreliable. "
            "Company is a growth stock, not an income stock."
        )

    # Sanity: growth rate cannot exceed discount rate
    if g_rate >= r:
        g_rate = r * 0.60   # Force g = 60% of r
        note = f"Dividend growth capped at {g_rate*100:.1f}% (was >= discount rate)"
    else:
        note = ""

    # ── Gordon Growth Model ────────────────────────────────────────────────
    d1 = dps * (1 + g_rate)   # Next year's expected dividend
    iv = d1 / (r - g_rate)

    # PSU Note: Use 3Y avg DPS if this is a PSU
    is_psu = data.get("is_psu", False)
    if is_psu:
        note += " | PSU: DPS may vary with government policy — IV is indicative"

    return {
        "model"          : "DDM",
        "iv"             : round(iv, 2),
        "d1"             : round(d1, 2),
        "dps"            : round(dps, 2),
        "growth_rate"    : round(g_rate * 100, 1),
        "required_return": round(r * 100, 1),
        "dividend_yield" : round(div_yield, 2),
        "inputs_used"    : {
            "dps"        : dps,
            "d1"         : round(d1, 2),
            "growth"     : f"{g_rate*100:.1f}%",
            "req_return" : f"{r*100:.1f}%",
            "div_yield"  : f"{div_yield:.2f}%",
        },
        "note"  : note.strip(" |"),
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model": "DDM", "iv": None, "d1": None,
        "dps": None, "growth_rate": None,
        "required_return": None, "dividend_yield": None,
        "inputs_used": {}, "note": reason, "valid": False
    }
