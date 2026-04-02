# =============================================================================
# screening/detector.py — Auto Stock Type Classifier
# Reads sector + financials and decides which valuation models to use.
#
# Stock Types:
#   BANK_NBFC    — Banks, NBFCs, Insurance, Diversified Financials
#   PSU          — Government-owned companies
#   EARLY_STAGE  — Loss-making or pre-profit companies
#   CYCLICAL     — Steel, Cement, Metals, Chemicals
#   HIGH_GROWTH  — IT, Pharma with high EPS growth
#   LARGE_STABLE — FMCG, mature consumer companies
#   GENERAL      — Everything else (runs all 6 base models)
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BANKING_SECTORS, PSU_KEYWORDS, IT_SECTORS, PHARMA_SECTORS,
    CYCLICAL_SECTORS, FMCG_SECTORS,
    CYCLICAL_REVENUE_STD_PCT, LOSS_MAKING_YEARS_THRESHOLD
)


# Stock type constants
BANK_NBFC    = "BANK_NBFC"
PSU          = "PSU"
EARLY_STAGE  = "EARLY_STAGE"
CYCLICAL     = "CYCLICAL"
HIGH_GROWTH  = "HIGH_GROWTH"
LARGE_STABLE = "LARGE_STABLE"
GENERAL      = "GENERAL"
REIT         = "REIT"


# REIT / InvIT detection keywords
REIT_KEYWORDS  = ["reit", "real estate investment trust", "invit",
                  "infrastructure investment trust"]
REIT_TICKERS   = {
    "EMBASSY", "MINDSPACE", "BIRET", "NEXUS",
    "IRBINVIT", "INDIGRID", "NHAI",
}


def detect(data: dict) -> dict:
    """
    Main detection function.
    Returns a dict:
      {
        "stock_type": str,
        "reason": str,
        "models_to_use": list,
        "models_to_skip": list,
        "weights": dict,
        "warning": str or None
      }
    """
    sector   = (data.get("sector") or "").strip()
    industry = (data.get("industry") or "").strip()
    name     = (data.get("name") or "").upper()
    symbol   = (data.get("symbol") or "").replace(".NS", "").upper()
    is_psu   = data.get("is_psu", False)

    eps_growth    = data.get("eps_growth_5y") or 0
    revenue_std   = data.get("revenue_std_pct") or 0
    dps           = data.get("dps") or 0
    rev_growth    = data.get("revenue_growth_5y") or 0
    np_series     = data.get("net_profit_5y") or []
    is_profitable = data.get("is_profitable", True)

    # ── Rule 0: REIT / InvIT — NAV-based valuation ────────────────────────
    combined_str = f"{sector} {industry} {name}".lower()
    is_reit = (
        symbol in REIT_TICKERS
        or any(kw in combined_str for kw in REIT_KEYWORDS)
    )
    if is_reit:
        return _result(
            stock_type    = REIT,
            reason        = f"REIT/InvIT: {name}",
            models_to_use = ["nav", "ddm", "relative"],
            models_to_skip= ["graham", "dcf", "lynch", "epv",
                              "excess_returns", "mid_cycle", "ev_sales",
                              "buffett", "price_tam"],
            weights       = {"nav": 0.70, "ddm": 0.30},
            warning       = (
                "ℹ REIT/InvIT: Using NAV model (book value of assets) + "
                "Distribution Yield. P/E not applicable."
            )
        )

    # ── Rule 1: EARLY STAGE — Loss-making + Price/TAM routing ─────────────
    losses = sum(1 for v in np_series[-3:] if v is not None and v < 0)
    if losses >= LOSS_MAKING_YEARS_THRESHOLD or not is_profitable:
        return _result(
            stock_type    = EARLY_STAGE,
            reason        = f"Loss-making in {losses} of last 3 years",
            models_to_use = ["ev_sales", "price_tam", "relative"],
            models_to_skip= ["graham", "dcf", "lynch", "epv", "ddm",
                              "buffett", "excess_returns", "mid_cycle", "nav"],
            weights       = {"ev_sales": 0.45, "price_tam": 0.35,
                             "relative": 0.20},
            warning       = (
                "⚠ EARNINGS-BASED VALUATION NOT APPLICABLE\n"
                "  Using EV/Sales (45%) + Price/TAM (35%) + Relative (20%). "
                "Early-stage estimates carry high uncertainty."
            )
        )

    # ── Rule 2: PSU ────────────────────────────────────────────────────────
    if is_psu or any(k.upper() in name for k in PSU_KEYWORDS):
        return _result(
            stock_type    = PSU,
            reason        = "Government-owned enterprise",
            models_to_use = ["ddm", "ev_ebitda", "graham", "relative"],
            models_to_skip= ["dcf", "lynch", "excess_returns",
                              "mid_cycle", "ev_sales", "nav", "price_tam"],
            weights       = {"ddm": 0.45, "ev_ebitda": 0.35, "graham": 0.20},
            warning       = (
                "ℹ PSU: Using 3Y average dividend for DDM (PSU payouts vary)"
            )
        )

    # ── Rule 3: BANK / NBFC ────────────────────────────────────────────────
    if any(s.lower() in sector.lower() for s in BANKING_SECTORS) or \
       any(s.lower() in industry.lower() for s in BANKING_SECTORS):
        return _result(
            stock_type    = BANK_NBFC,
            reason        = f"Financial sector: {sector}",
            models_to_use = ["excess_returns", "epv", "relative"],
            models_to_skip= ["dcf", "ev_ebitda", "lynch", "mid_cycle",
                              "buffett", "ev_sales", "nav", "price_tam"],
            weights       = {"excess_returns": 0.6, "epv": 0.4},
            warning       = None
        )

    # ── Rule 4: CYCLICAL — Steel, Cement, Metals, Chemicals ───────────────
    is_cyclical_sector = any(
        s.lower() in sector.lower() or s.lower() in industry.lower()
        for s in CYCLICAL_SECTORS
    )
    if is_cyclical_sector or revenue_std >= CYCLICAL_REVENUE_STD_PCT:
        reason = (
            f"Cyclical sector: {sector}" if is_cyclical_sector
            else f"High revenue volatility ({revenue_std*100:.1f}%)"
        )
        return _result(
            stock_type    = CYCLICAL,
            reason        = reason,
            models_to_use = ["mid_cycle", "relative"],
            models_to_skip= ["graham", "dcf", "lynch", "ddm",
                              "excess_returns", "ev_sales", "buffett",
                              "nav", "price_tam"],
            weights       = {"mid_cycle": 0.70, "relative": 0.30},
            warning       = (
                "⚠ CYCLICAL: Using MID-CYCLE EV/EBITDA (7Y average)\n"
                "  DO NOT use current P/E — it is misleading for cyclicals"
            )
        )

    # ── Rule 5: HIGH GROWTH — IT / Pharma ─────────────────────────────────
    is_it     = any(s.lower() in sector.lower() for s in IT_SECTORS)
    is_pharma = any(s.lower() in sector.lower() for s in PHARMA_SECTORS)
    if (is_it or is_pharma) and eps_growth > 0.10:
        pharma_note = (
            "ℹ PHARMA: Stage 1 DCF growth discounted 30% for pipeline risk"
            if is_pharma else None
        )
        return _result(
            stock_type    = HIGH_GROWTH,
            reason        = f"High-growth {sector}: EPS CAGR {eps_growth*100:.1f}%",
            models_to_use = ["dcf", "lynch", "graham", "relative"],
            models_to_skip= ["ddm", "epv", "excess_returns",
                              "mid_cycle", "ev_sales", "nav", "price_tam"],
            weights       = {"dcf": 0.50, "lynch": 0.30, "graham": 0.20},
            warning       = pharma_note
        )

    # ── Rule 6: LARGE STABLE — FMCG / Consumer ────────────────────────────
    is_fmcg = any(s.lower() in sector.lower() for s in FMCG_SECTORS)
    if is_fmcg or (dps > 0 and eps_growth < 0.15):
        return _result(
            stock_type    = LARGE_STABLE,
            reason        = f"Stable dividend-paying company: {sector}",
            models_to_use = ["dcf", "ddm", "graham", "epv", "relative"],
            models_to_skip= ["lynch", "excess_returns", "mid_cycle",
                              "ev_sales", "nav", "price_tam"],
            weights       = {"dcf": 0.40, "ddm": 0.30, "graham": 0.20, "epv": 0.10},
            warning       = None
        )

    # ── Default: GENERAL — Run all base models equally ────────────────────
    return _result(
        stock_type    = GENERAL,
        reason        = f"General classification: {sector}",
        models_to_use = ["dcf", "graham", "lynch", "buffett", "epv", "relative"],
        models_to_skip= ["excess_returns", "mid_cycle", "ev_sales",
                         "nav", "price_tam"],
        weights       = {
            "dcf": 0.35, "graham": 0.25,
            "lynch": 0.20, "epv": 0.20
        },
        warning       = None
    )


def _result(stock_type, reason, models_to_use, models_to_skip, weights, warning):
    return {
        "stock_type"    : stock_type,
        "reason"        : reason,
        "models_to_use" : models_to_use,
        "models_to_skip": models_to_skip,
        "weights"       : weights,
        "warning"       : warning
    }


def describe(detection: dict) -> str:
    """Return a human-readable string of the detection result."""
    lines = [
        f"  Stock Type  : {detection['stock_type']}",
        f"  Reason      : {detection['reason']}",
        f"  Models      : {', '.join(detection['models_to_use'])}",
    ]
    if detection.get("warning"):
        lines.append(f"  {detection['warning']}")
    return "\n".join(lines)
