# =============================================================================
# data/cleaner.py — Data Normaliser & Missing Value Handler
# Ensures all valuation modules receive clean, usable numbers
# =============================================================================

import sys, os
from typing import Union, List, Dict, Tuple
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DISCOUNT_RATE_LARGE_CAP, GSEC_10Y_YIELD, TERMINAL_GROWTH_RATE
)


def clean(data: dict) -> dict:
    """
    Takes raw fetched data dict and fills in missing values with
    sensible India-specific fallbacks. Returns cleaned data dict.
    """
    if data is None:
        return None

    d = data.copy()

    # ── EPS TTM ───────────────────────────────────────────────────────────
    if not d.get("eps_ttm") and d.get("net_profit_ttm") and d.get("shares_outstanding"):
        d["eps_ttm"] = d["net_profit_ttm"] / d["shares_outstanding"]
        _note(d, "eps_ttm", "computed from net_profit / shares")

    # ── EPS GROWTH ─────────────────────────────────────────────────────────
    if not d.get("eps_growth_5y"):
        # Try from net profit CAGR
        from data.fetcher import _cagr
        d["eps_growth_5y"] = _cagr(d.get("net_profit_5y", []))
        if d["eps_growth_5y"]:
            _note(d, "eps_growth_5y", "estimated from net profit CAGR")
        else:
            d["eps_growth_5y"] = 0.10  # Conservative 10% default
            _note(d, "eps_growth_5y", "defaulted to 10% (data unavailable)")

    # ── BOOK VALUE PER SHARE ───────────────────────────────────────────────
    if not d.get("book_value_per_share"):
        equity  = _latest(d.get("equity_5y", []))
        shares  = d.get("shares_outstanding")
        if equity and shares and shares > 0:
            d["book_value_per_share"] = equity / shares
            _note(d, "book_value_per_share", "computed from equity / shares")

    # ── DIVIDEND PER SHARE ─────────────────────────────────────────────────
    if not d.get("dps"):
        d["dps"] = 0.0
        _note(d, "dps", "no dividend data — assumed 0")

    # ── DIVIDEND GROWTH ────────────────────────────────────────────────────
    if not d.get("dps_growth_5y"):
        if d.get("dps", 0) > 0:
            d["dps_growth_5y"] = 0.05   # Conservative 5% default for dividend payers
            _note(d, "dps_growth_5y", "defaulted to 5%")
        else:
            d["dps_growth_5y"] = 0.0

    # ── FCF ────────────────────────────────────────────────────────────────
    if not d.get("fcf_5y"):
        # Compute FCF = Operating Cash Flow − Capex
        op_cf  = d.get("operating_cf_5y", [])
        capex  = d.get("capex_5y", [])
        if op_cf and capex:
            fcf_list = []
            for ocf, cap in zip(op_cf, capex):
                if ocf is not None and cap is not None:
                    fcf_list.append(ocf - abs(cap))
                else:
                    fcf_list.append(None)
            d["fcf_5y"] = fcf_list
            _note(d, "fcf_5y", "computed as OCF − Capex")

    # ── EBITDA ─────────────────────────────────────────────────────────────
    if not d.get("ebitda_ttm"):
        ebit = d.get("ebit_ttm")
        depr = d.get("depreciation_ttm")
        if ebit and depr:
            d["ebitda_ttm"] = ebit + depr
            _note(d, "ebitda_ttm", "computed as EBIT + Depreciation")

    # ── DEPRECIATION ───────────────────────────────────────────────────────
    if not d.get("depreciation_ttm"):
        d["depreciation_ttm"] = 0
        _note(d, "depreciation_ttm", "not found — set to 0")

    # ── CAPEX ──────────────────────────────────────────────────────────────
    if not d.get("capex_ttm"):
        d["capex_ttm"] = 0
        _note(d, "capex_ttm", "not found — set to 0")

    # ── TAX RATE ───────────────────────────────────────────────────────────
    if not d.get("tax_rate") or d["tax_rate"] <= 0 or d["tax_rate"] > 0.5:
        d["tax_rate"] = 0.25
        _note(d, "tax_rate", "defaulted to 25% (India corporate tax)")

    # ── DEBT / EQUITY ──────────────────────────────────────────────────────
    if d.get("debt_equity") is None:
        total_debt = d.get("total_debt", 0) or 0
        equity = _latest(d.get("equity_5y", []))
        if equity and equity > 0:
            d["debt_equity"] = total_debt / equity
            _note(d, "debt_equity", "computed from balance sheet")
        else:
            d["debt_equity"] = 0.0

    # ── INTEREST COVERAGE ──────────────────────────────────────────────────
    if d.get("interest_coverage") is None:
        ebit = d.get("ebit_ttm", 0) or 0
        ie   = d.get("interest_exp_ttm", 0) or 0
        if ie > 0:
            d["interest_coverage"] = ebit / ie
        else:
            d["interest_coverage"] = 999   # No debt → coverage is infinite

    # ── CURRENT RATIO ──────────────────────────────────────────────────────
    if d.get("current_ratio") is None:
        d["current_ratio"] = 1.5   # Neutral default
        _note(d, "current_ratio", "defaulted to 1.5 (data unavailable)")

    # ── ROE ────────────────────────────────────────────────────────────────
    roe_vals = [r for r in (d.get("roe_5y") or []) if r is not None]
    if not roe_vals:
        np_ttm = d.get("net_profit_ttm")
        eq_ttm = _latest(d.get("equity_5y", []))
        if np_ttm and eq_ttm and eq_ttm > 0:
            d["roe_5y"] = [np_ttm / eq_ttm]
            _note(d, "roe_5y", "computed from latest year only")
        else:
            d["roe_5y"] = [0.12]   # Neutral 12% default
            _note(d, "roe_5y", "defaulted to 12%")

    # ── REVENUE GROWTH ─────────────────────────────────────────────────────
    if not d.get("revenue_growth_5y"):
        d["revenue_growth_5y"] = 0.10
        _note(d, "revenue_growth_5y", "defaulted to 10%")

    # ── GROSS MARGIN ───────────────────────────────────────────────────────
    if not d.get("gross_margin_5y"):
        d["gross_margin_5y"] = [None]

    # ── BETA ───────────────────────────────────────────────────────────────
    if not d.get("beta") or d["beta"] <= 0:
        d["beta"] = 1.0
        _note(d, "beta", "defaulted to 1.0")

    # ── CMP FALLBACK ───────────────────────────────────────────────────────
    if not d.get("cmp") and d.get("eps_ttm") and d.get("pe_ratio"):
        d["cmp"] = d["eps_ttm"] * d["pe_ratio"]
        _note(d, "cmp", "computed from EPS × P/E")

    # ── EV FALLBACK ────────────────────────────────────────────────────────
    if not d.get("ev") and d.get("market_cap"):
        d["ev"] = d["market_cap"] + (d.get("total_debt") or 0) - (d.get("cash") or 0)

    # ── TTM-LINEARIZATION (Data Scaling) ───────────────────────────────────
    # If TTM Revenue > Annual Revenue, the company has grown since the last 
    # annual report. Scale annual-only metrics (Capex, FCF) up to TTM levels.
    ttm_rev = d.get("revenue_ttm")
    ann_rev = _latest(d.get("revenue_5y", []))
    
    if ttm_rev and ann_rev and ann_rev > 0:
        scaling_factor = max(0.8, min(ttm_rev / ann_rev, 1.5)) # Cap between 0.8x and 1.5x
        if abs(scaling_factor - 1.0) > 0.05: # Only scale if difference > 5%
            # Scale Capex TTM (if it came from annual)
            if d.get("capex_ttm"):
                d["capex_ttm"] *= scaling_factor
            
            # Scale FCF seed (if it came from annual series)
            if d.get("fcf_5y"):
                d["fcf_5y"] = [v * scaling_factor if v is not None else None for v in d["fcf_5y"]]
            
            # Scale Depreciation
            if d.get("depreciation_ttm"):
                d["depreciation_ttm"] *= scaling_factor
            
            _note(d, "ttm_linearization", f"scaled annual metrics by {scaling_factor:.2f}x to match TTM revenue")

    return d


def validate(data: dict) -> Tuple[bool, List]:
    """
    Returns (is_valid, list_of_warnings).
    Checks that critical data points exist for running any valuation.
    """
    warnings = []
    critical_missing = []

    required = ["cmp", "symbol", "name"]
    for key in required:
        if not data.get(key):
            critical_missing.append(key)

    # EPS needed for Graham, Lynch, Buffett earnings yield
    if not data.get("eps_ttm"):
        warnings.append("EPS missing — Graham, Lynch, Earnings Yield will be skipped")

    # FCF needed for DCF
    fcf = data.get("fcf_5y", [])
    if not fcf or all(v is None for v in fcf):
        warnings.append("FCF missing — DCF model will use Net Profit as proxy")

    # Dividend needed for DDM
    if not data.get("dps") or data["dps"] == 0:
        warnings.append("No dividend data — DDM will be skipped")

    # Book value needed for P/B / Excess Returns
    if not data.get("book_value_per_share"):
        warnings.append("Book Value missing — P/B and Excess Returns model will be skipped")

    is_valid = len(critical_missing) == 0
    if critical_missing:
        warnings.insert(0, f"CRITICAL MISSING: {', '.join(critical_missing)}")

    return is_valid, warnings


def avg_roe(data: dict) -> float:
    """Return average ROE from roe_5y list."""
    vals = [r for r in (data.get("roe_5y") or []) if r is not None]
    return sum(vals) / len(vals) if vals else None


def avg_gross_margin(data: dict) -> float:
    """Return average gross margin."""
    vals = [m for m in (data.get("gross_margin_5y") or []) if m is not None]
    return sum(vals) / len(vals) if vals else None


def avg_fcf(data: dict) -> float:
    """Return average FCF over available years (for DCF seed)."""
    fcf = data.get("fcf_5y") or []
    vals = [v for v in fcf if v is not None]
    return sum(vals) / len(vals) if vals else None


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _latest(series: list):
    if not series:
        return None
    for v in series:
        if v is not None:
            return v
    return None


def _note(data: dict, field: str, msg: str):
    """Record a note that a field was filled in / estimated."""
    if "_notes" not in data:
        data["_notes"] = {}
    data["_notes"][field] = msg
