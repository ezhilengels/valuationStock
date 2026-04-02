# =============================================================================
# valuation/epv.py — Earnings Power Value (Greenwald / Columbia Method)
#
# EPV = Adjusted EBIT × (1 − Tax Rate) / WACC
#
# No growth assumed — pure current earning power.
# If CMP < EPV → cheap even with zero growth.
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_discount_rate


def calculate(data: dict) -> dict:
    """
    Returns:
      {
        "model"        : "EPV",
        "iv"           : float or None,
        "adj_ebit"     : float,
        "nopat"        : float,   # EBIT × (1 - tax)
        "wacc"         : float,
        "tax_rate"     : float,
        "inputs_used"  : dict,
        "note"         : str,
        "valid"        : bool
      }
    """
    ebit_list  = data.get("ebit_5y") or []
    tax_rate   = data.get("tax_rate") or 0.25
    shares     = data.get("shares_outstanding")
    mkt_cap    = data.get("market_cap") or 0
    cash       = data.get("cash") or 0
    debt       = data.get("total_debt") or 0
    beta       = data.get("beta") or 1.0

    # ── Adjusted EBIT: 3-year average to smooth out one-offs ───────────────
    ebit_vals = [v for v in ebit_list[:3] if v is not None and v > 0]
    if not ebit_vals:
        return _invalid("EBIT data unavailable — EPV cannot be computed")

    adj_ebit = sum(ebit_vals) / len(ebit_vals)

    if adj_ebit <= 0:
        return _invalid("Adjusted EBIT is negative — EPV not applicable")

    # ── WACC / Ke ─────────────────────────────────────────────────────────
    wacc = get_discount_rate(beta)

    # ── NOPAT = Net Operating Profit After Tax ─────────────────────────────
    # Normalize tax rate: cap between 15% and 40%
    tax_rate = max(0.15, min(0.40, tax_rate))
    nopat    = adj_ebit * (1 - tax_rate)

    # ── EPV = NOPAT / WACC ─────────────────────────────────────────────────
    total_epv    = nopat / wacc
    equity_value = total_epv + cash - debt   # Enterprise → Equity

    if not shares or shares <= 0:
        return _invalid("Shares outstanding missing")

    iv_per_share = equity_value / shares

    note = (
        f"EBIT averaged over {len(ebit_vals)} year(s). "
        f"Zero growth assumed (pure earning power today)."
    )

    return {
        "model"       : "EPV",
        "iv"          : round(max(iv_per_share, 0), 2),
        "adj_ebit"    : round(adj_ebit, 2),
        "nopat"       : round(nopat, 2),
        "wacc"        : round(wacc * 100, 1),
        "tax_rate"    : round(tax_rate * 100, 1),
        "inputs_used" : {
            "adj_ebit_cr" : round(adj_ebit / 1e7, 1),
            "tax_rate"    : f"{tax_rate*100:.1f}%",
            "wacc"        : f"{wacc*100:.1f}%",
            "nopat_cr"    : round(nopat / 1e7, 1),
            "years_avg"   : len(ebit_vals),
        },
        "note"  : note,
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model": "EPV", "iv": None,
        "adj_ebit": None, "nopat": None,
        "wacc": None, "tax_rate": None,
        "inputs_used": {}, "note": reason, "valid": False
    }
