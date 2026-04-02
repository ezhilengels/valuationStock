# =============================================================================
# valuation/mid_cycle.py — Mid-Cycle EV/EBITDA (Cyclical Stocks)
#
# Steel, Cement, Aluminium, Chemicals, Metals
#
# KEY RULE: NEVER use current-year EPS or P/E for cyclicals.
# Use normalised mid-cycle EBITDA (7-year average).
#
# Method:
#   Mid-Cycle EBITDA = Average EBITDA over last 7 years
#   Target EV = Mid-Cycle EBITDA × Sector Multiple
#   Implied Price = (Target EV − Debt + Cash) / Shares
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CYCLICAL_LOOKBACK_YEARS


# Sector EV/EBITDA multiples for Indian cyclicals (mid-cycle)
SECTOR_MULTIPLES = {
    "steel"       : 6.0,
    "cement"      : 9.0,
    "aluminium"   : 6.5,
    "copper"      : 7.0,
    "mining"      : 5.5,
    "chemicals"   : 8.0,
    "fertilizers" : 6.0,
    "paint"       : 14.0,   # Asset-light, commands premium
    "tyres"       : 7.0,
    "plastics"    : 7.5,
    "default"     : 7.0,    # Generic cyclical
}


def calculate(data: dict, override_multiple: float = None) -> dict:
    """
    override_multiple: Force a specific EV/EBITDA multiple. If None, auto-detect.

    Returns:
      {
        "model"              : "MidCycleEV",
        "iv"                 : float or None,
        "mid_cycle_ebitda"   : float,
        "current_ebitda"     : float,
        "ebitda_vs_midcycle" : str,   # above/below/near
        "multiple_used"      : float,
        "implied_ev"         : float,
        "years_averaged"     : int,
        "cycle_position"     : str,   # PEAK / TROUGH / MID
        "warning"            : str,
        "inputs_used"        : dict,
        "note"               : str,
        "valid"              : bool
      }
    """
    ebitda_list = data.get("ebitda_5y") or []
    shares      = data.get("shares_outstanding")
    debt        = data.get("total_debt") or 0
    cash        = data.get("cash") or 0
    sector      = (data.get("sector") or "").lower()
    industry    = (data.get("industry") or "").lower()
    ev_ebitda   = data.get("ev_ebitda")

    # ── Validation ─────────────────────────────────────────────────────────
    ebitda_vals = [v for v in ebitda_list if v is not None and v > 0]
    if not ebitda_vals:
        return _invalid("EBITDA data unavailable — Mid-Cycle model cannot run")
    if not shares or shares <= 0:
        return _invalid("Shares outstanding missing")

    # ── Mid-Cycle EBITDA (average of available years, up to 7) ────────────
    years_used      = min(len(ebitda_vals), CYCLICAL_LOOKBACK_YEARS)
    mid_cycle_ebitda= sum(ebitda_vals[:years_used]) / years_used
    current_ebitda  = ebitda_vals[0]   # Most recent year

    if mid_cycle_ebitda <= 0:
        return _invalid("Mid-cycle EBITDA is zero or negative")

    # ── Cycle Position ────────────────────────────────────────────────────
    ratio = current_ebitda / mid_cycle_ebitda
    if ratio > 1.25:
        cycle_position = "PEAK (current EBITDA >> mid-cycle — may look cheap but isn't)"
        position_warning = True
    elif ratio < 0.75:
        cycle_position = "TROUGH (current EBITDA << mid-cycle — may look expensive but isn't)"
        position_warning = True
    else:
        cycle_position = "MID-CYCLE (current EBITDA near normalised level)"
        position_warning = False

    # ── EV/EBITDA Multiple ────────────────────────────────────────────────
    if override_multiple:
        multiple = override_multiple
        source   = "user override"
    else:
        multiple = _lookup_multiple(sector, industry)
        source   = "sector benchmark"

    # ── Implied EV & Per Share Price ──────────────────────────────────────
    implied_ev     = mid_cycle_ebitda * multiple
    equity_value   = implied_ev - debt + cash
    equity_value   = max(equity_value, 0)
    iv_per_share   = equity_value / shares

    # ── Current vs Mid-cycle EBITDA ───────────────────────────────────────
    pct_diff = (current_ebitda - mid_cycle_ebitda) / mid_cycle_ebitda * 100
    if pct_diff > 10:
        ebitda_status = f"Current EBITDA is {pct_diff:.0f}% ABOVE mid-cycle"
    elif pct_diff < -10:
        ebitda_status = f"Current EBITDA is {abs(pct_diff):.0f}% BELOW mid-cycle"
    else:
        ebitda_status = "Current EBITDA is near mid-cycle level"

    warning = (
        "⚠ CYCLICAL STOCK: DO NOT use current P/E ratio — it is misleading. "
        "This model uses normalised mid-cycle EBITDA instead."
    )
    if position_warning:
        warning += f"\n  ⚠ {cycle_position}"

    note = (
        f"Mid-cycle EBITDA averaged over {years_used} years. "
        f"EV/EBITDA multiple {multiple}x from {source}."
    )

    return {
        "model"              : "MidCycleEV",
        "iv"                 : round(iv_per_share, 2),
        "mid_cycle_ebitda"   : round(mid_cycle_ebitda, 2),
        "current_ebitda"     : round(current_ebitda, 2),
        "ebitda_vs_midcycle" : ebitda_status,
        "multiple_used"      : multiple,
        "implied_ev"         : round(implied_ev, 2),
        "years_averaged"     : years_used,
        "cycle_position"     : cycle_position,
        "warning"            : warning,
        "inputs_used"        : {
            "mid_cycle_ebitda_cr" : round(mid_cycle_ebitda / 1e7, 1),
            "current_ebitda_cr"   : round(current_ebitda / 1e7, 1),
            "multiple"            : multiple,
            "years_avg"           : years_used,
        },
        "note"  : note,
        "valid" : True
    }


def _lookup_multiple(sector: str, industry: str) -> float:
    combined = sector + " " + industry
    for keyword, multiple in SECTOR_MULTIPLES.items():
        if keyword in combined:
            return multiple
    return SECTOR_MULTIPLES["default"]


def _invalid(reason: str) -> dict:
    return {
        "model": "MidCycleEV", "iv": None,
        "mid_cycle_ebitda": None, "current_ebitda": None,
        "ebitda_vs_midcycle": None, "multiple_used": None,
        "implied_ev": None, "years_averaged": None,
        "cycle_position": None, "warning": None,
        "inputs_used": {}, "note": reason, "valid": False
    }
