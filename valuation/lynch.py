# =============================================================================
# valuation/lynch.py — Peter Lynch PEG Method
#
# Fair Value P/E  = EPS Growth Rate %
# Fair Value IV   = EPS × EPS Growth Rate %
# PEG Ratio       = (Current P/E) / EPS Growth Rate %
#
# PEG < 1   → Undervalued
# PEG 1–2   → Fairly Valued
# PEG > 2   → Overvalued
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def calculate(data: dict) -> dict:
    """
    Returns:
      {
        "model"          : "Lynch",
        "iv"             : float or None,
        "fair_pe"        : float,
        "current_pe"     : float,
        "peg_ratio"      : float,
        "peg_verdict"    : str,
        "inputs_used"    : dict,
        "note"           : str,
        "valid"          : bool
      }
    """
    eps      = data.get("eps_ttm")
    g_rate   = data.get("eps_growth_5y")   # decimal, e.g. 0.18 = 18%
    cmp      = data.get("cmp")
    curr_pe  = data.get("pe_ratio")

    # ── Validation ────────────────────────────────────────────────────────
    if not eps or eps <= 0:
        return _invalid("EPS is missing or negative — Lynch not applicable")
    if not g_rate or g_rate <= 0:
        return _invalid("EPS growth rate unavailable — Lynch requires growth data")

    g_pct = g_rate * 100   # e.g. 18% → use 18 in formula

    # Cap growth for formula sanity (Lynch himself cautioned > 25% is unreliable)
    g_pct_capped = min(g_pct, 25.0)
    note = ""
    if g_pct > 25:
        note = f"Growth capped at 25% (actual: {g_pct:.1f}%) per Lynch guidance"

    # ── Fair Value ────────────────────────────────────────────────────────
    fair_pe = g_pct_capped              # Fair P/E = growth rate %
    iv      = eps * g_pct_capped        # IV = EPS × growth%

    # ── PEG Ratio ─────────────────────────────────────────────────────────
    if not curr_pe and cmp and eps > 0:
        curr_pe = cmp / eps

    if curr_pe and g_pct > 0:
        peg = curr_pe / g_pct
        if peg < 1.0:
            peg_verdict = "UNDERVALUED (PEG < 1)"
        elif peg <= 2.0:
            peg_verdict = "FAIRLY VALUED (PEG 1–2)"
        else:
            peg_verdict = "OVERVALUED (PEG > 2)"
    else:
        peg = None
        peg_verdict = "N/A (P/E unavailable)"

    return {
        "model"       : "Lynch",
        "iv"          : round(iv, 2),
        "fair_pe"     : round(fair_pe, 1),
        "current_pe"  : round(curr_pe, 1) if curr_pe else None,
        "peg_ratio"   : round(peg, 2) if peg else None,
        "peg_verdict" : peg_verdict,
        "inputs_used" : {
            "eps"        : eps,
            "growth_pct" : f"{g_pct:.1f}%",
            "fair_pe"    : fair_pe,
        },
        "note"  : note,
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model": "Lynch", "iv": None, "fair_pe": None,
        "current_pe": None, "peg_ratio": None,
        "peg_verdict": "N/A", "inputs_used": {},
        "note": reason, "valid": False
    }
