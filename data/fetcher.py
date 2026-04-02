# =============================================================================
# data/fetcher.py — Live NSE Stock Data Fetcher
#
# Fetch order:
#   1. Check cache (30-min TTL) → return immediately on hit
#   2. Fetch from yfinance (.NS suffix)
#   3. Patch missing Indian-specific fields from screener.in
#   4. Store enriched result in cache
#   5. Return combined data dict
#
# Screener.in enrichment adds:
#   promoter_holding, promoter_pledge, fii_holding, dii_holding,
#   roce_ttm, book_value (cross-check), roce_10y, roe_10y (extended)
# =============================================================================

import yfinance as yf
import pandas as pd
import numpy as np
import sys
import os
from typing import Union, List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NSE_SUFFIX

# ── Lazy imports for cache and screener (avoids circular import) ──────────────
def _get_cache():
    from data.cache import get_cached, set_cache
    return get_cached, set_cache

def _get_screener():
    from data.screener import fetch_screener_data
    return fetch_screener_data


# =============================================================================
# PUBLIC API
# =============================================================================

def fetch_gsec_yield() -> float:
    """
    Fetch the live India 10-year G-Sec yield from yfinance (^IN10Y).
    Returns yield as a decimal (e.g. 0.0712 for 7.12%).
    Falls back to the config default if fetch fails.
    """
    try:
        ticker = yf.Ticker("^IN10Y")
        data = ticker.history(period="1d")
        if not data.empty:
            val = float(data["Close"].iloc[-1])
            # If yfinance returns it as 7.12, convert to 0.0712
            if val > 1.0:
                return val / 100.0
            return val
    except Exception:
        pass
    
    # Fallback to a safe Indian average if API fails
    return 0.070


def get_ticker(symbol: str):
    """Return yfinance Ticker object. Appends .NS if not present."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol = symbol + NSE_SUFFIX
    return yf.Ticker(symbol), symbol


def fetch_stock_data(symbol: str, use_cache: bool = True,
                     use_screener: bool = True) -> Union[dict, None]:
    """
    Master fetch function. Returns a dict with ALL data needed
    for every valuation model.

    Args:
        symbol       : NSE ticker (e.g. "INFY" or "INFY.NS")
        use_cache    : Check + populate 30-min cache (default True)
        use_screener : Enrich with screener.in fallback data (default True)

    Keys returned:
      symbol, name, sector, industry, cmp, market_cap,
      shares_outstanding, eps_ttm, eps_growth_5y,
      book_value_per_share, dps, dps_growth_5y,
      revenue_5y, net_profit_5y, fcf_5y,
      depreciation_ttm, capex_ttm, ebit_ttm, ebitda_ttm,
      total_debt, cash, roe_5y, gross_margin_5y,
      revenue_growth_5y, debt_equity, interest_coverage,
      current_ratio, tax_rate, beta,
      pe_ratio, pb_ratio, ev, ev_ebitda,
      is_profitable (bool), is_psu (bool),
      # From screener.in (when available):
      promoter_holding, promoter_pledge, fii_holding, dii_holding,
      roce_ttm, roe_10y, roce_10y, screener_ok
    """
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper().strip()

    # ── Step 1: Cache hit? ───────────────────────────────────────────────────
    if use_cache:
        try:
            get_cached, _ = _get_cache()
            cached = get_cached(clean_symbol, "main")
            if cached:
                print(f"  [Cache] Returning cached data for {clean_symbol}")
                return cached
        except Exception:
            pass   # Cache unavailable — continue to live fetch

    # ── Step 2: Fetch from yfinance ──────────────────────────────────────────
    ticker, full_symbol = get_ticker(clean_symbol)

    print(f"\n  Fetching data for {full_symbol}...")

    try:
        info        = ticker.info
        financials  = ticker.financials          # Annual P&L (columns = years)
        balance     = ticker.balance_sheet       # Annual Balance Sheet
        cashflow    = ticker.cashflow            # Annual Cash Flow
        fast_info   = ticker.fast_info
    except Exception as e:
        print(f"  [ERROR] Could not fetch data: {e}")
        return None

    # Sanity check — if info is completely empty, yfinance silently failed
    if not info or info.get("symbol") is None and info.get("shortName") is None:
        print(f"  [ERROR] No data returned by yfinance for {full_symbol}. "
              f"Check that the ticker is listed on NSE.")
        return None

    data = {}
    data["symbol"]  = full_symbol
    data["name"]    = info.get("longName") or info.get("shortName") or clean_symbol
    data["sector"]  = info.get("sector", "Unknown")
    data["industry"]= info.get("industry", "Unknown")

    # ── PRICE ────────────────────────────────────────────────────────────────
    data["cmp"] = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or _safe_fast(fast_info, "last_price")
        or None
    )

    # ── SHARES & MARKET CAP ──────────────────────────────────────────────────
    data["shares_outstanding"] = (
        info.get("sharesOutstanding")
        or _safe_fast(fast_info, "shares")
    )
    data["market_cap"] = info.get("marketCap", None)

    # ── PER-SHARE METRICS ────────────────────────────────────────────────────
    data["eps_ttm"]             = info.get("trailingEps", None)
    data["book_value_per_share"]= info.get("bookValue", None)
    data["dps"]                 = info.get("dividendRate", None)   # Annual DPS
    data["pe_ratio"]            = info.get("trailingPE", None)
    data["pb_ratio"]            = info.get("priceToBook", None)
    data["beta"]                = info.get("beta", 1.0) or 1.0

    # ── 5-YEAR TIME SERIES ───────────────────────────────────────────────────
    data["revenue_5y"]     = _extract_series(financials, ["Total Revenue"])
    data["net_profit_5y"]  = _extract_series(financials, ["Net Income",
                                                           "Net Income Common Stockholders"])
    data["ebit_5y"]        = _extract_series(financials, ["EBIT", "Operating Income"])
    data["ebitda_5y"]      = _extract_series(financials, ["EBITDA", "Normalized EBITDA"])
    data["interest_exp_5y"]= _extract_series(financials, ["Interest Expense"])
    data["gross_profit_5y"]= _extract_series(financials, ["Gross Profit"])

    # ── BALANCE SHEET ────────────────────────────────────────────────────────
    data["total_debt_5y"]  = _extract_series(balance, ["Total Debt", "Long Term Debt"])
    data["cash_5y"]        = _extract_series(balance, ["Cash And Cash Equivalents",
                                                        "Cash Cash Equivalents And Short Term Investments"])
    data["equity_5y"]      = _extract_series(balance, ["Stockholders Equity",
                                                        "Total Stockholders Equity"])
    data["current_assets"] = _extract_series(balance, ["Current Assets"])
    data["current_liab"]   = _extract_series(balance, ["Current Liabilities"])

    # ── CASH FLOW ────────────────────────────────────────────────────────────
    data["fcf_5y"]          = _extract_series(cashflow, ["Free Cash Flow"])
    data["capex_5y"]        = _extract_series(cashflow, ["Capital Expenditure", "Purchase Of PPE"])
    data["depreciation_5y"] = _extract_series(cashflow, ["Depreciation And Amortization",
                                                          "Depreciation Amortization Depletion"])
    data["operating_cf_5y"] = _extract_series(cashflow, ["Operating Cash Flow"])

    # ── LATEST SINGLES ───────────────────────────────────────────────────────
    data["ebit_ttm"]         = _latest(data["ebit_5y"])
    data["ebitda_ttm"]       = _latest(data["ebitda_5y"])
    data["capex_ttm"]        = abs(_latest(data["capex_5y"]) or 0)
    data["depreciation_ttm"] = _latest(data["depreciation_5y"])
    data["total_debt"]       = _latest(data["total_debt_5y"])
    data["cash"]             = _latest(data["cash_5y"])
    data["revenue_ttm"]      = _latest(data["revenue_5y"])
    data["net_profit_ttm"]   = _latest(data["net_profit_5y"])
    data["interest_exp_ttm"] = abs(_latest(data["interest_exp_5y"]) or 0)

    # ── COMPUTED RATIOS ──────────────────────────────────────────────────────
    mc = data["market_cap"] or 0
    td = data["total_debt"] or 0
    ca = data["cash"] or 0
    data["ev"] = mc + td - ca

    ebitda = data["ebitda_ttm"]
    data["ev_ebitda"] = (data["ev"] / ebitda) if ebitda and ebitda > 0 else None

    rev = data["revenue_ttm"]
    data["ev_sales"] = (data["ev"] / rev) if rev and rev > 0 else None

    data["roe_5y"]          = _compute_roe(data["net_profit_5y"], data["equity_5y"])
    data["gross_margin_5y"] = _compute_margins(data["gross_profit_5y"], data["revenue_5y"])
    data["revenue_growth_5y"]= _cagr(data["revenue_5y"])
    data["eps_growth_5y"]   = _cagr(data["net_profit_5y"])
    data["dps_growth_5y"]   = _dividend_growth(ticker)

    equity_latest = _latest(data["equity_5y"])
    data["debt_equity"] = (
        (data["total_debt"] / equity_latest)
        if equity_latest and equity_latest > 0 else None
    )

    ie = data["interest_exp_ttm"]
    eb = data["ebit_ttm"]
    data["interest_coverage"] = (eb / ie) if ie and ie > 0 and eb else None

    ca_val = _latest(data["current_assets"])
    cl_val = _latest(data["current_liab"])
    data["current_ratio"] = (
        (ca_val / cl_val) if ca_val and cl_val and cl_val > 0 else None
    )

    data["tax_rate"]        = _compute_tax_rate(financials)
    data["revenue_std_pct"] = _std_pct(data["revenue_5y"])

    np_series = [v for v in (data["net_profit_5y"] or []) if v is not None]
    losses = sum(1 for v in np_series[-3:] if v < 0)
    data["is_profitable"] = losses < 2

    from config import PSU_KEYWORDS
    name_upper = data["name"].upper()
    data["is_psu"] = any(k.upper() in name_upper for k in PSU_KEYWORDS)

    # ── Step 3: Screener.in enrichment ──────────────────────────────────────
    if use_screener:
        data = _enrich_from_screener(clean_symbol, data)

    # ── Step 4: Store in cache ───────────────────────────────────────────────
    if use_cache:
        try:
            _, set_cache = _get_cache()
            set_cache(clean_symbol, data, "main")
        except Exception:
            pass   # Non-fatal — continue without caching

    print(f"  ✓ Data ready for {data['name']}")
    return data


# =============================================================================
# SCREENER.IN ENRICHMENT
# =============================================================================

def _enrich_from_screener(symbol: str, data: dict) -> dict:
    """
    Fetch Indian-specific fields from screener.in and merge them into data.
    Only patches fields that are None/missing in yfinance output.
    """
    # Fields we want from screener that yfinance doesn't reliably provide
    WANT_FIELDS = [
        "promoter_holding", "promoter_pledge", "fii_holding", "dii_holding",
        "public_holding", "roce_ttm", "roe_10y", "roce_10y",
        "eps_10y", "sales_10y", "net_profit_10y", "current_ratio",
    ]

    any_missing = (
        data.get("promoter_holding") is None
        or data.get("fii_holding") is None
        or data.get("roce_ttm") is None
    )

    if not any_missing:
        return data   # yfinance had everything we need — skip screener

    try:
        fetch_screener = _get_screener()
        sc = fetch_screener(symbol)

        if not sc.get("screener_ok"):
            data["screener_ok"] = False
            return data

        # Merge — only fill None / missing fields, don't overwrite good yfinance data
        for field in WANT_FIELDS:
            if field in sc and sc[field] is not None:
                if data.get(field) is None:
                    data[field] = sc[field]

        # Always capture screener metadata fields
        data["screener_ok"]      = sc.get("screener_ok", False)
        data["screener_source"]  = sc.get("data_source", "")

        # Cross-check: if yfinance book value is absent, use screener's
        if data.get("book_value_per_share") is None and sc.get("book_value"):
            data["book_value_per_share"] = sc["book_value"]

        # Cross-check: if yfinance current_ratio is absent, use screener's
        if data.get("current_ratio") is None and sc.get("current_ratio"):
            data["current_ratio"] = sc["current_ratio"]

        # Cross-check: D/E from screener when yfinance misses it
        if data.get("debt_equity") is None and sc.get("debt_equity_screener"):
            data["debt_equity"] = sc["debt_equity_screener"]

        # Extend roe_5y with screener's 10-year if we have fewer than 3 points
        if sc.get("roe_10y") and len([r for r in (data.get("roe_5y") or []) if r]) < 3:
            data["roe_10y_screener"] = sc["roe_10y"]
            # Use last 5 of 10-year screener data as fallback roe_5y
            if not data.get("roe_5y") or len(data["roe_5y"]) < 2:
                data["roe_5y"] = sc["roe_10y"][-5:]

        print(f"  ✓ Screener.in data merged ({sc.get('data_source', '')})")

    except Exception as ex:
        # Screener.in is a fallback — never crash the main flow
        data["screener_ok"] = False
        print(f"  [Screener] Skipped ({ex})")

    return data


# =============================================================================
# HELPERS
# =============================================================================

def _safe_fast(fast_info, key: str):
    """Safely read from fast_info (which may be a dict or object)."""
    try:
        if isinstance(fast_info, dict):
            return fast_info.get(key)
        return getattr(fast_info, key, None)
    except Exception:
        return None


def _extract_series(df: pd.DataFrame, row_names: list) -> list:
    """Extract a time series (newest first) for given row names."""
    if df is None or df.empty:
        return []
    for name in row_names:
        if name in df.index:
            vals = df.loc[name].dropna().tolist()
            return [float(v) if v is not None else None for v in vals]
    return []


def _latest(series: list):
    """Return the most recent (first) non-None value from a series."""
    if not series:
        return None
    for v in series:
        if v is not None:
            return v
    return None


def _cagr(series: list) -> Union[float, None]:
    """Compute CAGR from a list of values (newest first)."""
    vals = [v for v in series if v is not None and v != 0]
    if len(vals) < 2:
        return None
    start = vals[-1]
    end   = vals[0]
    years = len(vals) - 1
    if start <= 0 or end <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def _compute_roe(net_profit_series: list, equity_series: list) -> list:
    """Return list of annual ROE values (same length as inputs)."""
    roes = []
    for np_val, eq_val in zip(net_profit_series or [], equity_series or []):
        if np_val is not None and eq_val and eq_val > 0:
            roes.append(np_val / eq_val)
        else:
            roes.append(None)
    return roes


def _compute_margins(numerator: list, denominator: list) -> list:
    """Return list of ratio values."""
    margins = []
    for n, d in zip(numerator or [], denominator or []):
        if n is not None and d and d > 0:
            margins.append(n / d)
        else:
            margins.append(None)
    return margins


def _dividend_growth(ticker: yf.Ticker) -> Union[float, None]:
    """Compute 5Y dividend CAGR from dividend history."""
    try:
        hist = ticker.dividends
        if hist.empty:
            return None
        hist = hist.resample("YE").sum()
        vals = hist.dropna().tolist()
        if len(vals) < 2:
            return None
        return _cagr(list(reversed(vals)))
    except Exception:
        return None


def _compute_tax_rate(financials: pd.DataFrame) -> float:
    """Estimate effective tax rate from latest year."""
    try:
        pretax = None
        tax    = None
        for row in ["Pretax Income", "Income Before Tax"]:
            if row in financials.index:
                pretax = financials.loc[row].dropna().iloc[0]
                break
        for row in ["Tax Provision", "Income Tax Expense"]:
            if row in financials.index:
                tax = financials.loc[row].dropna().iloc[0]
                break
        if pretax and tax and pretax > 0:
            return abs(float(tax)) / float(pretax)
    except Exception:
        pass
    return 0.25   # Default: 25% India corporate tax rate


def _std_pct(series: list) -> Union[float, None]:
    """Coefficient of variation (std / mean) for cyclical detection."""
    vals = [v for v in series if v is not None and v > 0]
    if len(vals) < 3:
        return None
    arr  = np.array(vals)
    mean = np.mean(arr)
    if mean == 0:
        return None
    return float(np.std(arr) / mean)


# =============================================================================
# DEBUG UTILITY
# =============================================================================

def print_raw_data(data: dict):
    """Pretty-print raw fetched data for debugging/inspection."""
    try:
        from colorama import Fore, Style, init
        init(autoreset=True)
    except ImportError:
        pass

    cmp_str = f"₹{data['cmp']:,.2f}" if data.get("cmp") else "N/A"
    mc_str  = (f"₹{data['market_cap']/1e7:,.0f} Cr"
               if data.get("market_cap") else "N/A")

    def _fmt_pct(val):
        return f"{val*100:.1f}%" if val is not None else "N/A"

    print(f"\n{'='*60}")
    print(f"  RAW DATA — {data['name']} ({data['symbol']})")
    print(f"{'='*60}")
    print(f"  Sector        : {data.get('sector', 'N/A')}")
    print(f"  Industry      : {data.get('industry', 'N/A')}")
    print(f"  CMP           : {cmp_str}")
    print(f"  Market Cap    : {mc_str}")
    print()
    print(f"  EPS (TTM)     : ₹{data['eps_ttm']}" if data.get("eps_ttm") else "  EPS (TTM)     : N/A")
    print(f"  EPS Growth    : {_fmt_pct(data.get('eps_growth_5y'))} CAGR")
    print(f"  Book Value    : ₹{data['book_value_per_share']}" if data.get("book_value_per_share") else "  Book Value    : N/A")
    print(f"  DPS           : ₹{data['dps']}" if data.get("dps") else "  DPS           : N/A")
    print()
    print(f"  P/E           : {data['pe_ratio']:.1f}x" if data.get("pe_ratio") else "  P/E           : N/A")
    print(f"  P/B           : {data['pb_ratio']:.1f}x" if data.get("pb_ratio") else "  P/B           : N/A")
    print(f"  EV/EBITDA     : {data['ev_ebitda']:.1f}x" if data.get("ev_ebitda") else "  EV/EBITDA     : N/A")
    print(f"  EV/Sales      : {data['ev_sales']:.1f}x" if data.get("ev_sales") else "  EV/Sales      : N/A")
    print()
    roe_vals = [r for r in (data.get("roe_5y") or []) if r is not None]
    avg_roe  = sum(roe_vals) / len(roe_vals) if roe_vals else None
    print(f"  ROE (avg)     : {_fmt_pct(avg_roe)}")
    print(f"  D/E Ratio     : {data['debt_equity']:.2f}" if data.get("debt_equity") is not None else "  D/E Ratio     : N/A")
    print(f"  Int Cover     : {data['interest_coverage']:.1f}x" if data.get("interest_coverage") else "  Int Cover     : N/A")
    print(f"  Curr Ratio    : {data['current_ratio']:.2f}" if data.get("current_ratio") else "  Curr Ratio    : N/A")
    print()
    print(f"  EBIT (TTM)    : ₹{data['ebit_ttm']/1e7:,.0f} Cr" if data.get("ebit_ttm") else "  EBIT (TTM)    : N/A")
    print(f"  EBITDA (TTM)  : ₹{data['ebitda_ttm']/1e7:,.0f} Cr" if data.get("ebitda_ttm") else "  EBITDA (TTM)  : N/A")
    print(f"  Capex (TTM)   : ₹{data['capex_ttm']/1e7:,.0f} Cr" if data.get("capex_ttm") else "  Capex (TTM)   : N/A")
    print(f"  Depr (TTM)    : ₹{data['depreciation_ttm']/1e7:,.0f} Cr" if data.get("depreciation_ttm") else "  Depr (TTM)    : N/A")
    print()
    print(f"  Rev Growth    : {_fmt_pct(data.get('revenue_growth_5y'))} CAGR")
    print(f"  Tax Rate      : {_fmt_pct(data.get('tax_rate'))}")
    print(f"  Is PSU        : {data.get('is_psu', False)}")
    print(f"  Profitable    : {data.get('is_profitable', False)}")
    print()
    # Screener enrichment section
    if data.get("screener_ok"):
        print(f"  ── Screener.in Enrichment ({data.get('screener_source', '')}) ──")
        print(f"  Promoter      : {_fmt_pct(data.get('promoter_holding'))}")
        print(f"  Pledge        : {_fmt_pct(data.get('promoter_pledge'))}")
        print(f"  FII           : {_fmt_pct(data.get('fii_holding'))}")
        print(f"  DII           : {_fmt_pct(data.get('dii_holding'))}")
        print(f"  ROCE (TTM)    : {_fmt_pct(data.get('roce_ttm'))}")
    elif data.get("screener_ok") is False:
        print("  Screener.in   : Not available")
    print(f"{'='*60}\n")
