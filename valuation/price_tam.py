# =============================================================================
# valuation/price_tam.py — Price / TAM (Total Addressable Market) Model
#
# Used for: EARLY_STAGE stocks — startups, new-age tech, fintech, EV players
#            that have no earnings but growing revenues.
#
# Philosophy (inspired by Damodaran's Revenue-Based Valuation):
#   • TAM = estimated total addressable market for the company's segment
#   • Market Share % = realistic share the company can capture at maturity
#   • Target Revenue = TAM × Market Share %
#   • Terminal Net Margin = sector-median margin the company should reach
#   • Terminal Net Profit = Target Revenue × Terminal Margin
#   • Terminal Value = Terminal Net Profit × Exit PE
#   • IV = Terminal Value × (1 + growth)^N / (1 + r)^N    [PV today]
#
# Default TAM assumptions (₹ Crores) — can be overridden via config:
#   These are rough order-of-magnitude estimates for Indian market segments.
#   Analyst/sector-specific TAMs will always be more accurate.
#
# Output: iv, terminal_revenue, terminal_profit, mos, note, valid, inputs_used
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


# ── Sector TAM Defaults (₹ Crores, Indian market) ────────────────────────────
# Sources: NASSCOM, RedSeer, IBEF, Motilal Oswal sector reports (2024 estimates)
SECTOR_TAM_CR = {
    # Digital / Fintech
    "fintech"            : 1_000_000,   # ₹10 lakh Cr (~$120B)
    "payments"           : 800_000,
    "insurance tech"     : 300_000,
    "wealthtech"         : 200_000,

    # E-commerce / D2C
    "e-commerce"         : 1_200_000,   # ₹12 lakh Cr by 2030
    "direct to consumer" : 150_000,

    # SaaS / Cloud / IT Services
    "saas"               : 180_000,
    "cloud"              : 250_000,
    "edtech"             : 80_000,
    "healthtech"         : 180_000,
    "agritech"           : 60_000,

    # EV / Clean Energy
    "electric vehicle"   : 500_000,
    "clean energy"       : 350_000,
    "solar"              : 200_000,

    # Logistics / Supply Chain
    "logistics"          : 400_000,
    "supply chain"       : 300_000,

    # Real estate tech / PropTech
    "proptech"           : 120_000,
    "real estate tech"   : 120_000,

    # Default for anything unclassified
    "default"            : 100_000,   # ₹1 lakh Cr
}

# ── Terminal Net Margin assumptions by sector ─────────────────────────────────
SECTOR_TERMINAL_MARGIN = {
    "fintech"        : 0.20,
    "payments"       : 0.18,
    "saas"           : 0.25,
    "cloud"          : 0.22,
    "e-commerce"     : 0.08,
    "edtech"         : 0.15,
    "healthtech"     : 0.15,
    "electric vehicle": 0.12,
    "clean energy"   : 0.14,
    "solar"          : 0.12,
    "logistics"      : 0.10,
    "default"        : 0.12,
}

# ── Market Share assumptions (at maturity in 10-15Y) ─────────────────────────
# Conservative: 1–5% market share for most early-stage companies
DEFAULT_MARKET_SHARE = 0.03   # 3% of TAM

# ── Exit PE for early-stage companies at maturity ────────────────────────────
DEFAULT_EXIT_PE = 30   # Growth company PE at maturity


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def calculate(data: dict) -> dict:
    """
    Price/TAM valuation for early-stage companies.

    Args:
        data: Enriched data dict from fetcher + cleaner

    Returns:
        {
          "iv"              : float  Intrinsic Value per share (₹),
          "terminal_revenue": float  ₹ Crores at maturity,
          "terminal_profit" : float  ₹ Crores at maturity,
          "market_share"    : float  Assumed market share fraction,
          "tam_cr"          : float  Assumed TAM in ₹ Crores,
          "exit_pe"         : int,
          "discount_rate"   : float,
          "years_to_maturity": int,
          "note"            : str,
          "valid"           : bool,
          "inputs_used"     : dict,
        }
    """
    cmp           = data.get("cmp") or 0
    sector        = (data.get("sector") or "").lower()
    industry      = (data.get("industry") or "").lower()
    shares        = data.get("shares_outstanding") or 0
    revenue_ttm   = data.get("revenue_ttm") or 0
    rev_growth_5y = data.get("revenue_growth_5y") or 0
    mkt_cap       = data.get("market_cap") or 0
    market_cap_cr = mkt_cap / 1e7   # Convert ₹ to ₹ Crores

    # ── Validate inputs ───────────────────────────────────────────────────────
    if shares <= 0:
        return _skip("Cannot compute: shares outstanding not available")
    if revenue_ttm <= 0:
        return _skip("Cannot compute: zero or negative revenue")
    if market_cap_cr <= 0:
        return _skip("Cannot compute: market cap not available")

    # Revenue in Crores
    revenue_cr = revenue_ttm / 1e7

    # ── Find sector TAM ───────────────────────────────────────────────────────
    tam_cr       = _find_tam(sector, industry)
    terminal_margin = _find_terminal_margin(sector, industry)
    market_share = DEFAULT_MARKET_SHARE

    # ── Market Share Adjustment ───────────────────────────────────────────────
    # If company already has significant revenue, they may capture more share
    if tam_cr > 0 and revenue_cr > 0:
        current_share = revenue_cr / tam_cr
        # Cap market share between 0.5% and 15%
        market_share = max(0.005, min(0.15, max(current_share * 3, DEFAULT_MARKET_SHARE)))

    # ── Revenue Growth Rate (for 10Y projection) ──────────────────────────────
    # Use a blend: observed 5Y growth with decay assumption
    if rev_growth_5y and rev_growth_5y > 0:
        stage1_growth = min(rev_growth_5y, 0.60)   # Cap at 60%
    else:
        stage1_growth = 0.25   # Default 25% for early-stage

    # ── Years to Maturity ─────────────────────────────────────────────────────
    # How many years until company reaches TAM-based terminal revenue
    # We use 10 years as standard horizon for early-stage
    years = 10
    discount_rate = cfg.DISCOUNT_RATE_LARGE_CAP + 0.04   # Higher risk = +4%

    # ── Terminal Revenue (at maturity) ────────────────────────────────────────
    terminal_revenue_cr = tam_cr * market_share

    # Alternative: project current revenue forward at blended growth
    rev_at_maturity_growth = revenue_cr * (1 + stage1_growth) ** (years // 2) \
                             * (1 + stage1_growth * 0.4) ** (years // 2)
    # Take the lower of the two (conservative)
    terminal_revenue_cr = min(terminal_revenue_cr, rev_at_maturity_growth)

    # ── Terminal Profit ───────────────────────────────────────────────────────
    terminal_profit_cr = terminal_revenue_cr * terminal_margin

    if terminal_profit_cr <= 0:
        return _skip("Terminal profit is zero — company unlikely to reach profitability")

    # ── Terminal Value ────────────────────────────────────────────────────────
    exit_pe       = DEFAULT_EXIT_PE
    terminal_value_cr = terminal_profit_cr * exit_pe

    # ── Present Value ─────────────────────────────────────────────────────────
    # Discount terminal value back to today
    pv_terminal_cr = terminal_value_cr / ((1 + discount_rate) ** years)

    # ── Probability Adjustment ─────────────────────────────────────────────────
    # Early-stage companies have execution risk — apply a haircut
    # Use a 50% probability of success for pure early-stage
    success_prob   = 0.50
    adjusted_pv_cr = pv_terminal_cr * success_prob

    # ── IV per share ──────────────────────────────────────────────────────────
    # Convert ₹ Crores to ₹ (×1e7), divide by shares outstanding
    iv = (adjusted_pv_cr * 1e7) / shares

    # ── EV/Sales cross-check (sanity check) ───────────────────────────────────
    # If implied EV/Sales > 30x current revenue, cap it conservatively
    if revenue_cr > 0:
        implied_ev_sales = (adjusted_pv_cr) / revenue_cr
        if implied_ev_sales > 30:
            # Too rich — cap IV at 30x EV/Sales
            iv = (30 * revenue_cr * 1e7) / shares

    note = (
        f"Price/TAM model: TAM ₹{tam_cr:,.0f} Cr × {market_share*100:.1f}% share "
        f"→ ₹{terminal_revenue_cr:,.0f} Cr rev at maturity | "
        f"Net margin {terminal_margin*100:.0f}% | Exit PE {exit_pe}x | "
        f"50% exec-risk haircut | WACC {discount_rate*100:.0f}%"
    )

    return {
        "iv"               : round(iv, 2),
        "terminal_revenue" : round(terminal_revenue_cr, 1),
        "terminal_profit"  : round(terminal_profit_cr, 1),
        "market_share"     : round(market_share, 4),
        "tam_cr"           : tam_cr,
        "exit_pe"          : exit_pe,
        "discount_rate"    : discount_rate,
        "years_to_maturity": years,
        "success_prob"     : success_prob,
        "note"             : note,
        "valid"            : True,
        "inputs_used"      : {
            "Revenue TTM (₹Cr)"     : round(revenue_cr, 1),
            "Rev Growth 5Y CAGR"    : f"{stage1_growth*100:.1f}%",
            "TAM (₹Cr)"             : tam_cr,
            "Market Share Assumed"  : f"{market_share*100:.1f}%",
            "Terminal Revenue (₹Cr)": round(terminal_revenue_cr, 1),
            "Terminal Net Margin"   : f"{terminal_margin*100:.0f}%",
            "Exit PE"               : exit_pe,
            "Discount Rate"         : f"{discount_rate*100:.0f}%",
            "Years to Maturity"     : years,
            "Success Probability"   : "50%",
        }
    }


# =============================================================================
# HELPERS
# =============================================================================

def _find_tam(sector: str, industry: str) -> float:
    """Find the closest TAM estimate from the sector/industry."""
    combined = f"{sector} {industry}".lower()
    for keyword, tam in SECTOR_TAM_CR.items():
        if keyword in combined:
            return float(tam)
    return float(SECTOR_TAM_CR["default"])


def _find_terminal_margin(sector: str, industry: str) -> float:
    """Find the terminal net margin assumption for the sector."""
    combined = f"{sector} {industry}".lower()
    for keyword, margin in SECTOR_TERMINAL_MARGIN.items():
        if keyword in combined:
            return margin
    return SECTOR_TERMINAL_MARGIN["default"]


def _skip(note: str) -> dict:
    return {
        "iv"   : None,
        "valid": False,
        "note" : note,
        "inputs_used": {}
    }
