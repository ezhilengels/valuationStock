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
    eps_ttm  = data.get("eps_ttm")
    g_rate   = data.get("eps_growth_5y")   # decimal, e.g. 0.18 = 18%
    cmp      = data.get("cmp")
    curr_pe  = data.get("pe_ratio")
    dps      = data.get("dps") or 0
    sector   = (data.get("sector") or "").lower()
    
    # ── 1. Average EPS (Smoothing) ────────────────────────────────────────
    # Institutional tools use a 3-year average to remove one-time peaks
    np_series = data.get("net_profit_5y") or []
    shares    = data.get("shares_outstanding")
    
    eps_avg_3y = None
    if shares and shares > 0:
        recent_np = [v for v in np_series[:3] if v is not None]
        if recent_np:
            eps_avg_3y = (sum(recent_np) / len(recent_np)) / shares
            
    # Use the lower of TTM or 3Y Average for a conservative Lynch value
    eps_to_use = min(eps_ttm, eps_avg_3y) if eps_avg_3y and eps_ttm else eps_ttm

    # ── Validation ────────────────────────────────────────────────────────
    if not eps_to_use or eps_to_use <= 0:
        return _invalid("EPS is missing or negative — Lynch not applicable")
    if not g_rate or g_rate <= 0:
        return _invalid("EPS growth rate unavailable — Lynch requires growth data")

    # ── 2. Adjusted Growth (Growth + Dividend Yield) ──────────────────────
    # Lynch's actual formula for "True Value" includes dividends
    div_yield = (dps / cmp * 100) if cmp and cmp > 0 else 0
    g_pct     = g_rate * 100
    lynch_multiplier = g_pct + div_yield

    # ── 3. Sector-Aware Growth Caps ────────────────────────────────────────
    # Large Caps cannot grow at 25%+ forever.
    # Pharma/IT: 20% max | Commodities: 15% max | General: 25% max
    cap = 25.0
    if "pharma" in sector or "healthcare" in sector:
        cap = 20.0
    elif "materials" in sector or "steel" in sector or "energy" in sector:
        cap = 15.0
        
    g_capped = min(lynch_multiplier, cap)
    
    note = f"Using {('TTM' if eps_to_use == eps_ttm else '3Y Avg')} EPS."
    if lynch_multiplier > cap:
        note += f" | Multiplier capped at {cap}% for {sector} sector."

    # ── 4. Fair Value ─────────────────────────────────────────────────────
    fair_pe = g_capped
    iv      = eps_to_use * g_capped

    # ── PEG Ratio ─────────────────────────────────────────────────────────
    if not curr_pe and cmp and eps_ttm > 0:
        curr_pe = cmp / eps_ttm

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
            "eps_used"   : round(eps_to_use, 2),
            "lynch_mult" : round(lynch_multiplier, 1),
            "div_yield"  : f"{div_yield:.1f}%",
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
