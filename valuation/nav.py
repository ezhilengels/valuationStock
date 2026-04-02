# =============================================================================
# valuation/nav.py — Net Asset Value (NAV) Model for REITs & InvITs
#
# Used for: Indian REITs and InvITs listed on NSE:
#   Embassy Office Parks REIT (EMBASSY), Mindspace REIT (MINDSPACE),
#   Brookfield India REIT (BIRET), Nexus Select Trust (NEXUS),
#   IRB InvIT (IRBINVIT), IndiGrid InvIT (INDIGRID), PowerGrid InvIT (POWERGRID)
#
# NAV-based valuation logic:
#   NAV = Total Assets − Total Liabilities (at fair / book value)
#   NAV per unit = NAV / Units outstanding
#   IV = NAV per unit × (1 + premium/discount to NAV)
#
# Adjustments made:
#   1. Debt haircut (Indian REITs must maintain specific LTV ratios)
#   2. Distributable Cash Flow (DCF) yield check — REITs pay 90%+ of income
#   3. P/NAV check — compare CMP vs declared NAV (from info or screener)
#   4. Distribution yield comparison vs G-Sec (replaces earnings yield)
#
# When NAV is declared:     use declared NAV directly
# When NAV is not declared: estimate from book value of assets
#
# India REIT context:
#   • SEBI mandates quarterly NAV declarations for REITs
#   • Typical premium: 0–30% to NAV for quality REITs
#   • Distribution yield: 6–8% (linked to rental income)
#   • LTV cap: 49% (strict SEBI regulation)
#
# Output: iv, nav_per_unit, p_nav, dist_yield, note, valid, inputs_used
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


# ── Known Indian REITs / InvITs (NSE tickers without .NS) ────────────────────
REIT_TICKERS = {
    # REITs (office / retail)
    "EMBASSY"    : {"type": "REIT", "sector": "Office",  "premium_cap": 0.30},
    "MINDSPACE"  : {"type": "REIT", "sector": "Office",  "premium_cap": 0.25},
    "BIRET"      : {"type": "REIT", "sector": "Office",  "premium_cap": 0.25},
    "NEXUS"      : {"type": "REIT", "sector": "Retail",  "premium_cap": 0.20},
    # InvITs (infrastructure)
    "IRBINVIT"   : {"type": "InvIT", "sector": "Roads",   "premium_cap": 0.15},
    "INDIGRID"   : {"type": "InvIT", "sector": "Power",   "premium_cap": 0.15},
    "POWERGRID"  : {"type": "InvIT", "sector": "Power",   "premium_cap": 0.15},
    "NHAI"       : {"type": "InvIT", "sector": "Roads",   "premium_cap": 0.10},
}

# Typical premium/discount to NAV by REIT quality
PREMIUM_TO_NAV = {
    "high_quality" : 0.20,   # 20% premium for top REITs (Embassy, Mindspace)
    "mid_quality"  : 0.10,
    "invit"        : 0.05,   # InvITs trade closer to NAV
}

# Sector-appropriate distribution yield targets
TARGET_DIST_YIELD = {
    "REIT"  : 0.065,   # 6.5% distribution yield
    "InvIT" : 0.075,   # 7.5% distribution yield (higher risk)
}


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def calculate(data: dict) -> dict:
    """
    NAV-based valuation for REITs and InvITs.

    Returns:
        {
          "iv"            : float  IV per unit (₹),
          "nav_per_unit"  : float  NAV per unit (₹),
          "p_nav"         : float  CMP / NAV per unit,
          "dist_yield"    : float  Distribution yield at CMP,
          "note"          : str,
          "valid"         : bool,
          "inputs_used"   : dict,
        }
    """
    symbol   = (data.get("symbol") or "").replace(".NS", "").upper()
    cmp      = data.get("cmp") or 0
    dps      = data.get("dps") or 0            # Distribution per unit (annual)
    bv_share = data.get("book_value_per_share") # Book value per unit
    shares   = data.get("shares_outstanding") or 0
    total_debt = data.get("total_debt") or 0
    mkt_cap  = data.get("market_cap") or 0
    equity   = None

    # Try equity from balance sheet
    eq_series = data.get("equity_5y") or []
    for v in eq_series:
        if v is not None and v > 0:
            equity = v
            break

    # ── Determine if this is a REIT / InvIT ───────────────────────────────
    reit_info = REIT_TICKERS.get(symbol)
    reit_type = "REIT"
    sector    = "Office"
    if reit_info:
        reit_type = reit_info["type"]
        sector    = reit_info["sector"]

    # ── Validate inputs ───────────────────────────────────────────────────
    if cmp <= 0:
        return _skip("CMP not available")

    if shares <= 0:
        return _skip("Units outstanding not available")

    # ── Step 1: Estimate NAV ──────────────────────────────────────────────
    # Priority order:
    # A) Book value per share (most accurate if yfinance has it)
    # B) Equity / shares
    # C) Fallback: market cap based estimate

    nav_per_unit = None
    nav_source   = "N/A"

    if bv_share and bv_share > 0:
        nav_per_unit = bv_share
        nav_source   = "yfinance book value"
    elif equity and equity > 0 and shares > 0:
        nav_per_unit = equity / shares
        nav_source   = "equity / shares"
    elif mkt_cap > 0:
        # Last resort: assume CMP is at 20% premium to NAV
        nav_per_unit = cmp / 1.20
        nav_source   = "CMP / 1.20x (estimated)"

    if not nav_per_unit or nav_per_unit <= 0:
        return _skip("Could not estimate NAV: book value and equity data missing")

    # ── Step 2: Distribution yield at CMP ────────────────────────────────
    dist_yield = (dps / cmp) if cmp > 0 and dps > 0 else None

    # ── Step 3: IV from Distribution Yield (DDM-like for REIT) ───────────
    # IV from yield = DPS / required distribution yield
    target_yield = TARGET_DIST_YIELD.get(reit_type, 0.065)
    gsec         = cfg.GSEC_10Y_YIELD
    required_yield = gsec + 0.015   # G-Sec + 150 bps risk premium for REITs

    iv_from_yield = None
    if dps > 0:
        iv_from_yield = dps / required_yield

    # ── Step 4: IV from NAV premium ───────────────────────────────────────
    # Decide if it's a quality REIT or InvIT
    if reit_type == "InvIT":
        quality_premium = PREMIUM_TO_NAV["invit"]
    elif symbol in {"EMBASSY", "MINDSPACE"}:
        quality_premium = PREMIUM_TO_NAV["high_quality"]
    else:
        quality_premium = PREMIUM_TO_NAV["mid_quality"]

    iv_from_nav = nav_per_unit * (1 + quality_premium)

    # ── Step 5: P/NAV ratio ───────────────────────────────────────────────
    p_nav = cmp / nav_per_unit if nav_per_unit > 0 else None

    # ── Step 6: Blend IVs ─────────────────────────────────────────────────
    # Weighted: 60% NAV-based, 40% yield-based (if yield available)
    if iv_from_yield:
        iv = iv_from_nav * 0.60 + iv_from_yield * 0.40
        blend_note = f"NAV-based IV ₹{iv_from_nav:,.0f} (60%) + Yield-based ₹{iv_from_yield:,.0f} (40%)"
    else:
        iv = iv_from_nav
        blend_note = f"NAV-based IV only (no distribution data)"

    # ── Step 7: LTV sanity check ──────────────────────────────────────────
    # SEBI caps REIT LTV at 49%. If total debt / (mkt cap + debt) > 49%,
    # it's a risk signal — apply 10% haircut
    ltv_flag = False
    if mkt_cap > 0 and total_debt > 0:
        ltv = total_debt / (mkt_cap + total_debt)
        if ltv > 0.49:
            iv   = iv * 0.90   # 10% LTV risk haircut
            ltv_flag = True

    # ── Construct note ────────────────────────────────────────────────────
    dist_str = f"{dist_yield*100:.2f}%" if dist_yield else "N/A"
    p_nav_str = f"{p_nav:.2f}x" if p_nav else "N/A"
    note = (
        f"{reit_type} NAV model | NAV/unit ₹{nav_per_unit:,.0f} ({nav_source}) | "
        f"P/NAV {p_nav_str} | Dist Yield {dist_str} vs required {required_yield*100:.1f}% | "
        f"{blend_note}"
        + (" | ⚠️ LTV >49% haircut applied" if ltv_flag else "")
    )

    return {
        "iv"           : round(iv, 2),
        "nav_per_unit" : round(nav_per_unit, 2),
        "p_nav"        : round(p_nav, 3) if p_nav else None,
        "dist_yield"   : round(dist_yield, 4) if dist_yield else None,
        "iv_from_nav"  : round(iv_from_nav, 2),
        "iv_from_yield": round(iv_from_yield, 2) if iv_from_yield else None,
        "reit_type"    : reit_type,
        "ltv_warning"  : ltv_flag,
        "note"         : note,
        "valid"        : True,
        "inputs_used"  : {
            "NAV per Unit (₹)"     : round(nav_per_unit, 2),
            "NAV Source"           : nav_source,
            "Distribution/Unit (₹)": dps,
            "Dist Yield at CMP"    : dist_str,
            "Required Yield"       : f"{required_yield*100:.1f}%",
            "Quality Premium"      : f"{quality_premium*100:.0f}%",
            "G-Sec Used"           : f"{gsec*100:.1f}%",
            "P/NAV"                : p_nav_str,
            "REIT Type"            : reit_type,
            "LTV Warning"          : ltv_flag,
        }
    }


# =============================================================================
# HELPERS
# =============================================================================

def _skip(note: str) -> dict:
    return {
        "iv"   : None,
        "valid": False,
        "note" : note,
        "inputs_used": {}
    }


def is_reit(data: dict) -> bool:
    """
    Quick check if a stock should use NAV model.
    Called from screening/detector.py
    """
    symbol  = (data.get("symbol") or "").replace(".NS", "").upper()
    sector  = (data.get("sector") or "").lower()
    industry= (data.get("industry") or "").lower()
    name    = (data.get("name") or "").upper()

    # Known REITs/InvITs by ticker
    if symbol in REIT_TICKERS:
        return True

    # Detect by sector/industry/name keywords
    reit_keywords = ["reit", "real estate investment trust", "invit",
                     "infrastructure investment trust"]
    combined = f"{sector} {industry} {name}".lower()
    return any(kw in combined for kw in reit_keywords)
