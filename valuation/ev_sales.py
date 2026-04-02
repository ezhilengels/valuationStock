# =============================================================================
# valuation/ev_sales.py — EV/Sales Model (Early Stage / Loss-Making Stocks)
#
# Used when: Net Profit < 0 for 2+ years (Zomato, Paytm, Nykaa type)
# Traditional earnings models BREAK for these — use EV/Sales instead.
#
# Method:
#   1. Compute current EV/Sales
#   2. Compare vs sector benchmarks and global peers
#   3. Apply a target EV/Sales to get implied fair value
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Global/India peer EV/Sales benchmarks by sector (update periodically)
EVSALES_BENCHMARKS = {
    "food delivery"       : 3.0,    # Zomato vs DoorDash, Delivery Hero
    "fintech"             : 4.0,    # Paytm vs global fintech
    "e-commerce"          : 2.5,    # Nykaa, Meesho, etc.
    "saas"                : 8.0,    # High-margin software
    "edtech"              : 2.0,    # Byju's, Unacademy comps
    "healthtech"          : 3.5,
    "default"             : 3.0,    # Generic fallback
}


def calculate(data: dict, target_ev_sales: float = None) -> dict:
    """
    target_ev_sales: Override the benchmark. If None, uses sector lookup.

    Returns:
      {
        "model"           : "EV/Sales",
        "iv"              : float or None,
        "current_ev_sales": float,
        "target_ev_sales" : float,
        "revenue_ttm_cr"  : float,
        "ev_cr"           : float,
        "upside_pct"      : float,
        "warning"         : str,
        "inputs_used"     : dict,
        "note"            : str,
        "valid"           : bool
      }
    """
    ev      = data.get("ev")
    rev     = data.get("revenue_ttm")
    shares  = data.get("shares_outstanding")
    cmp     = data.get("cmp")
    mkt_cap = data.get("market_cap")
    sector  = (data.get("sector") or "").lower()
    industry= (data.get("industry") or "").lower()

    # ── Validation ─────────────────────────────────────────────────────────
    if not rev or rev <= 0:
        return _invalid("Revenue data unavailable — EV/Sales cannot be computed")
    if not shares or shares <= 0:
        return _invalid("Shares outstanding missing")

    # ── Current EV/Sales ──────────────────────────────────────────────────
    if not ev and mkt_cap:
        debt = data.get("total_debt") or 0
        cash = data.get("cash") or 0
        ev = mkt_cap + debt - cash

    current_ev_sales = ev / rev if ev else None

    # ── Target EV/Sales (from benchmark or override) ───────────────────────
    if target_ev_sales:
        target   = target_ev_sales
        source   = "user-specified"
    else:
        target   = _lookup_benchmark(sector, industry)
        source   = "sector benchmark"

    # ── Implied Fair Market Cap ────────────────────────────────────────────
    debt = data.get("total_debt") or 0
    cash = data.get("cash") or 0

    implied_ev     = rev * target
    implied_mktcap = implied_ev - debt + cash
    implied_mktcap = max(implied_mktcap, 0)

    iv_per_share   = implied_mktcap / shares

    # ── Upside / Downside ─────────────────────────────────────────────────
    if cmp and cmp > 0:
        upside_pct = (iv_per_share - cmp) / cmp * 100
    else:
        upside_pct = None

    warning = (
        "⚠ EV/Sales is a relative metric, NOT an intrinsic value. "
        "Implied price depends heavily on the benchmark chosen. "
        "Use only for directional comparison vs peers."
    )

    note = (
        f"Target EV/Sales {target}x from {source}. "
        f"Revenue = ₹{rev/1e7:,.0f} Cr. "
        f"Implied EV = ₹{implied_ev/1e7:,.0f} Cr."
    )

    return {
        "model"            : "EV/Sales",
        "iv"               : round(iv_per_share, 2),
        "current_ev_sales" : round(current_ev_sales, 2) if current_ev_sales else None,
        "target_ev_sales"  : target,
        "revenue_ttm_cr"   : round(rev / 1e7, 1),
        "ev_cr"            : round(ev / 1e7, 1) if ev else None,
        "upside_pct"       : round(upside_pct, 1) if upside_pct else None,
        "warning"          : warning,
        "inputs_used"      : {
            "revenue_cr"    : round(rev / 1e7, 1),
            "target_ev_sales": target,
            "benchmark_src" : source,
        },
        "note"  : note,
        "valid" : True
    }


def _lookup_benchmark(sector: str, industry: str) -> float:
    combined = sector + " " + industry
    for keyword, multiple in EVSALES_BENCHMARKS.items():
        if keyword in combined:
            return multiple
    return EVSALES_BENCHMARKS["default"]


def _invalid(reason: str) -> dict:
    return {
        "model": "EV/Sales", "iv": None,
        "current_ev_sales": None, "target_ev_sales": None,
        "revenue_ttm_cr": None, "ev_cr": None,
        "upside_pct": None, "warning": None,
        "inputs_used": {}, "note": reason, "valid": False
    }
