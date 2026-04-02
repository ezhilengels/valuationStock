# =============================================================================
# valuation/dcf.py — 2-Stage Discounted Cash Flow
#
# Stage 1 (Years 1-5):  High growth phase
# Stage 2 (Years 6-10): Moderate growth = Stage1 × 0.5
# Terminal Value:        FCF10 × (1+g) / (r−g)
#
# IV per share = Total PV / Shares Outstanding
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DISCOUNT_RATE_LARGE_CAP, DISCOUNT_RATE_MID_CAP,
    TERMINAL_GROWTH_RATE, DCF_STAGE1_YEARS, DCF_STAGE2_YEARS,
    DCF_STAGE2_GROWTH_FACTOR
)
from data.cleaner import avg_fcf


def calculate(data: dict, pharma_haircut: bool = False) -> dict:
    """
    pharma_haircut: If True (Pharma sector), Stage 1 growth discounted 30%
    for pipeline uncertainty.

    Returns:
      {
        "model"         : "DCF",
        "iv"            : float or None,
        "total_pv"      : float,
        "terminal_value": float,
        "stage1_growth" : float,
        "stage2_growth" : float,
        "discount_rate" : float,
        "fcf_seed"      : float,
        "inputs_used"   : dict,
        "note"          : str,
        "valid"         : bool
      }
    """
    shares   = data.get("shares_outstanding")
    fcf_list = data.get("fcf_5y") or []
    mkt_cap  = data.get("market_cap") or 0
    g_rate   = data.get("eps_growth_5y") or 0.10
    net_prof = data.get("net_profit_5y") or []

    # ── FCF Seed ──────────────────────────────────────────────────────────
    # Use average FCF. If FCF unavailable, fall back to avg net profit.
    fcf_vals = [v for v in fcf_list if v is not None]
    np_vals  = [v for v in net_prof if v is not None]

    if fcf_vals:
        fcf_seed = sum(fcf_vals) / len(fcf_vals)
        fcf_source = "avg FCF"
    elif np_vals:
        fcf_seed = sum(np_vals) / len(np_vals)
        fcf_source = "avg Net Profit (FCF unavailable)"
    else:
        return _invalid("No FCF or Net Profit data available for DCF")

    if fcf_seed <= 0:
        return _invalid(
            "Negative average FCF — DCF not reliable. "
            "Check EV/Sales or other models for this stock."
        )

    # ── Growth Rates ──────────────────────────────────────────────────────
    stage1_growth = g_rate
    if pharma_haircut:
        stage1_growth = g_rate * 0.70   # 30% haircut for pipeline risk
    stage1_growth = min(stage1_growth, 0.35)   # Cap at 35% (sanity)

    stage2_growth = stage1_growth * DCF_STAGE2_GROWTH_FACTOR
    terminal_g    = TERMINAL_GROWTH_RATE           # 5.5%

    # ── Discount Rate (WACC) ──────────────────────────────────────────────
    if mkt_cap >= 20_000_00_00_000:    # > ₹20,000 Cr = Large cap
        r = DISCOUNT_RATE_LARGE_CAP    # 12%
    else:
        r = DISCOUNT_RATE_MID_CAP      # 14%

    if r <= terminal_g:
        return _invalid(f"Discount rate ({r}) must be > terminal growth ({terminal_g})")

    # ── Project Cash Flows ────────────────────────────────────────────────
    pv_cashflows = []
    fcf = fcf_seed

    # Stage 1: Years 1-5
    for yr in range(1, DCF_STAGE1_YEARS + 1):
        fcf = fcf * (1 + stage1_growth)
        pv  = fcf / ((1 + r) ** yr)
        pv_cashflows.append(pv)

    # Stage 2: Years 6-10
    for yr in range(DCF_STAGE1_YEARS + 1, DCF_STAGE1_YEARS + DCF_STAGE2_YEARS + 1):
        fcf = fcf * (1 + stage2_growth)
        pv  = fcf / ((1 + r) ** yr)
        pv_cashflows.append(pv)

    # ── Terminal Value ─────────────────────────────────────────────────────
    fcf_terminal = fcf * (1 + terminal_g)
    terminal_val = fcf_terminal / (r - terminal_g)
    pv_terminal  = terminal_val / ((1 + r) ** (DCF_STAGE1_YEARS + DCF_STAGE2_YEARS))

    # ── Total Intrinsic Value ─────────────────────────────────────────────
    total_pv = sum(pv_cashflows) + pv_terminal

    # Add cash, subtract debt for equity value
    cash = data.get("cash") or 0
    debt = data.get("total_debt") or 0
    equity_value = total_pv + cash - debt

    if not shares or shares <= 0:
        return _invalid("Shares outstanding missing — cannot compute per-share IV")

    iv_per_share = equity_value / shares

    note = f"FCF seed: {fcf_source}"
    if pharma_haircut:
        note += " | 30% pharma pipeline haircut applied to Stage 1 growth"

    return {
        "model"         : "DCF",
        "iv"            : round(max(iv_per_share, 0), 2),
        "total_pv"      : round(total_pv, 2),
        "terminal_value": round(pv_terminal, 2),
        "tv_pct"        : round(pv_terminal / total_pv * 100, 1) if total_pv > 0 else None,
        "stage1_growth" : round(stage1_growth * 100, 1),
        "stage2_growth" : round(stage2_growth * 100, 1),
        "discount_rate" : round(r * 100, 1),
        "fcf_seed"      : round(fcf_seed, 2),
        "inputs_used"   : {
            "fcf_seed"      : round(fcf_seed / 1e7, 2),   # in Crores
            "stage1_growth" : f"{stage1_growth*100:.1f}%",
            "stage2_growth" : f"{stage2_growth*100:.1f}%",
            "terminal_g"    : f"{terminal_g*100:.1f}%",
            "discount_rate" : f"{r*100:.1f}%",
        },
        "note"  : note,
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model": "DCF", "iv": None, "total_pv": None,
        "terminal_value": None, "tv_pct": None,
        "stage1_growth": None, "stage2_growth": None,
        "discount_rate": None, "fcf_seed": None,
        "inputs_used": {}, "note": reason, "valid": False
    }
