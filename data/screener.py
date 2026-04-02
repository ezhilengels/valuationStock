# =============================================================================
# data/screener.py — Screener.in Fallback for Indian-Specific Data
#
# yfinance misses several NSE-specific fields. This module scrapes
# screener.in as a fallback when those fields are absent.
#
# Data fetched from Screener.in:
#   • Promoter holding %        (insider ownership)
#   • Promoter pledge %         (debt risk signal)
#   • FII holding %             (institutional confidence)
#   • DII holding %             (domestic institutional)
#   • 10-year financial history (EPS, Sales, Net Profit, ROE)
#   • Debt-to-equity (more reliable than yfinance for Indian cos)
#   • Book Value per share
#   • Dividend yield (declared, not trailing)
#   • ROCE %                    (Return on Capital Employed)
#   • Current ratio
#   • P/E, P/B from screener    (cross-check with yfinance)
#
# Usage:
#   from data.screener import fetch_screener_data
#   extra = fetch_screener_data("INFY")   # No .NS suffix needed
#
# Returns a flat dict with all available fields, or {} on failure.
# All monetary values are in ₹ Crores (Screener.in convention).
# =============================================================================

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Union, List, Dict

# ── Constants ────────────────────────────────────────────────────────────────
BASE_URL      = "https://www.screener.in/company/{symbol}/consolidated/"
STANDALONE_URL= "https://www.screener.in/company/{symbol}/"
HEADERS       = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 12   # seconds
RETRY_DELAY     = 2    # seconds between retries
MAX_RETRIES     = 2


# =============================================================================
# PUBLIC API
# =============================================================================

def fetch_screener_data(symbol: str) -> dict:
    """
    Main entry point. Tries consolidated view first, falls back to standalone.
    Returns a dict with all extracted fields (empty dict on complete failure).

    Keys returned (all optional — may be None if not found):
        promoter_holding    float  e.g. 0.724 (72.4%)
        promoter_pledge     float  e.g. 0.05  (5%)
        fii_holding         float
        dii_holding         float
        public_holding      float
        roce_ttm            float  Return on Capital Employed
        current_ratio       float
        book_value          float  Book Value per share (₹)
        debt_equity_screener float
        pe_screener         float
        pb_screener         float
        div_yield_screener  float
        sales_10y           list   [float, ...] oldest → newest
        net_profit_10y      list
        eps_10y             list
        roe_10y             list
        data_source         str    "screener_consolidated" or "screener_standalone"
        screener_ok         bool
    """
    symbol = symbol.replace(".NS", "").upper().strip()

    # Try consolidated first (more complete for large caps)
    for url_template, source_label in [
        (BASE_URL,       "screener_consolidated"),
        (STANDALONE_URL, "screener_standalone"),
    ]:
        url  = url_template.format(symbol=symbol)
        html = _fetch_html(url)
        if html:
            result = _parse_screener_page(html)
            if result:
                result["data_source"]  = source_label
                result["screener_ok"]  = True
                return result

    # Complete failure
    return {
        "screener_ok" : False,
        "data_source" : "screener_failed",
    }


# =============================================================================
# HTML FETCH
# =============================================================================

def _fetch_html(url: str) -> Union[str, None]:
    """Fetch URL with retries. Returns HTML string or None."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                return None   # Symbol not found — don't retry
            else:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        except requests.RequestException:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


# =============================================================================
# PAGE PARSER
# =============================================================================

def _parse_screener_page(html: str) -> Union[dict, None]:
    """
    Parse screener.in HTML into a flat dict.
    Returns None if the page doesn't look like a valid company page.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Quick validity check — screener shows "We couldn't find" for bad symbols
    body_text = soup.get_text()
    if "couldn't find" in body_text.lower() or "404" in body_text[:200]:
        return None

    result = {}

    # ── Key Ratios (top section) ──────────────────────────────────────────
    result.update(_parse_key_ratios(soup))

    # ── Shareholding Pattern ──────────────────────────────────────────────
    result.update(_parse_shareholding(soup))

    # ── 10-Year Historical Data ────────────────────────────────────────────
    result.update(_parse_historical_tables(soup))

    return result if result else None


# =============================================================================
# KEY RATIOS SECTION
# =============================================================================

def _parse_key_ratios(soup: BeautifulSoup) -> dict:
    """
    Scrape the key ratios section (top of screener page).
    Contains: Market Cap, PE, PB, Div Yield, Book Value, ROCE, ROE, etc.
    """
    result = {}

    # Screener puts ratios in <li> items inside #top-ratios
    ratios_section = soup.find(id="top-ratios")
    if not ratios_section:
        # Fallback: look for the ratios list
        ratios_section = soup.find("ul", class_="ranges")

    if ratios_section:
        items = ratios_section.find_all("li")
        for item in items:
            label_tag = item.find("span", class_="name")
            value_tag = item.find("span", class_="number")
            if not label_tag or not value_tag:
                continue
            label = label_tag.get_text(strip=True).lower()
            value = _clean_number(value_tag.get_text(strip=True))

            if value is None:
                continue

            if "stock p/e" in label or "p/e" in label:
                result["pe_screener"] = value
            elif "price to book" in label or "p/b" in label:
                result["pb_screener"] = value
            elif "dividend yield" in label:
                result["div_yield_screener"] = value / 100
            elif "book value" in label:
                result["book_value"] = value
            elif "roce" in label:
                result["roce_ttm"] = value / 100
            elif "current ratio" in label:
                result["current_ratio"] = value
            elif "debt to equity" in label or "d/e" in label:
                result["debt_equity_screener"] = value

    # Also parse the "company-ratios" section (alternative layout)
    alt_section = soup.find("section", id="company-ratios")
    if alt_section and not result:
        for row in alt_section.find_all("li"):
            spans = row.find_all("span")
            if len(spans) >= 2:
                label = spans[0].get_text(strip=True).lower()
                value = _clean_number(spans[-1].get_text(strip=True))
                if value is None:
                    continue
                if "p/e" in label:
                    result.setdefault("pe_screener", value)
                elif "p/b" in label or "price to book" in label:
                    result.setdefault("pb_screener", value)
                elif "roce" in label:
                    result.setdefault("roce_ttm", value / 100)
                elif "book value" in label:
                    result.setdefault("book_value", value)
                elif "current ratio" in label:
                    result.setdefault("current_ratio", value)
                elif "div" in label and "yield" in label:
                    result.setdefault("div_yield_screener", value / 100)

    return result


# =============================================================================
# SHAREHOLDING SECTION
# =============================================================================

def _parse_shareholding(soup: BeautifulSoup) -> dict:
    """
    Extract promoter, FII, DII, and public holding percentages.
    Screener shows these in a table in the 'Shareholding Pattern' section.
    """
    result = {}

    # Find the shareholding section
    sh_section = (
        soup.find("section", id="shareholding")
        or soup.find(lambda t: t.name in ("section", "div")
                     and t.get_text()
                     and "shareholding" in t.get_text().lower()[:50])
    )

    if not sh_section:
        return result

    # Look for the most recent quarter's data (first data column)
    tables = sh_section.find_all("table")
    if not tables:
        return result

    table = tables[0]
    rows  = table.find_all("tr")

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True).lower()
        # First data column is most recent quarter
        value = _clean_number(cells[1].get_text(strip=True))
        if value is None:
            continue

        if "promoter" in label and "pledge" not in label:
            result["promoter_holding"] = value / 100
        elif "pledge" in label or "pledged" in label:
            result["promoter_pledge"] = value / 100
        elif "fii" in label or "foreign" in label:
            result["fii_holding"] = value / 100
        elif "dii" in label or "domestic" in label:
            result["dii_holding"] = value / 100
        elif "public" in label:
            result["public_holding"] = value / 100

    return result


# =============================================================================
# HISTORICAL TABLES (10-Year Financials)
# =============================================================================

def _parse_historical_tables(soup: BeautifulSoup) -> dict:
    """
    Scrape 10-year financial history tables:
      - Sales (Revenue)
      - Net Profit
      - EPS
      - ROE (from Key Metrics / Ratios table)
    """
    result = {}

    # Screener uses section IDs: profit-loss, balance-sheet, cash-flow, ratios
    pl_section = soup.find("section", id="profit-loss")
    if pl_section:
        tables = pl_section.find_all("table")
        if tables:
            tbl = tables[0]
            rows = tbl.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                label = cells[0].get_text(strip=True).lower()
                values = [_clean_number(c.get_text(strip=True)) for c in cells[1:]]
                values = [v for v in values if v is not None]

                if "sales" in label or "revenue" in label:
                    result["sales_10y"] = values
                elif "net profit" in label or "profit after" in label:
                    result["net_profit_10y"] = values
                elif label.strip() == "eps":
                    result["eps_10y"] = values

    # Ratios section for ROE and ROCE history
    ratios_section = soup.find("section", id="ratios")
    if ratios_section:
        tables = ratios_section.find_all("table")
        if tables:
            tbl  = tables[0]
            rows = tbl.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                label  = cells[0].get_text(strip=True).lower()
                values = [_clean_number(c.get_text(strip=True)) for c in cells[1:]]
                values = [v for v in values if v is not None]

                if "return on equity" in label or "roe" in label:
                    # Convert % to decimal
                    result["roe_10y"] = [v / 100 for v in values]
                elif "roce" in label:
                    result["roce_10y"] = [v / 100 for v in values]

    return result


# =============================================================================
# UTILITY
# =============================================================================

def _clean_number(text: str) -> Union[float, None]:
    """
    Convert screener.in formatted numbers to float.
    Handles: "1,234.56", "12.3%", "₹ 234", "2,34,567", "N/A", "--"
    """
    if not text:
        return None
    text = text.strip()

    # Remove currency symbols and percentage signs
    text = re.sub(r"[₹%,\s]", "", text)

    # Handle dash/N/A/blank
    if text in ("", "-", "--", "N/A", "NA", "n/a", "—"):
        return None

    # Handle negative in parentheses: (123) → -123
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]

    try:
        return float(text)
    except ValueError:
        return None


# =============================================================================
# CONVENIENCE HELPERS (called from fetcher.py)
# =============================================================================

def get_promoter_holding(symbol: str) -> Union[float, None]:
    """Quick helper — returns promoter holding % as decimal or None."""
    data = fetch_screener_data(symbol)
    return data.get("promoter_holding")


def get_shareholding_summary(symbol: str) -> dict:
    """
    Returns a clean dict with all holding percentages.
    Example: {"promoter": 0.724, "fii": 0.183, "dii": 0.054, "public": 0.039, "pledge": 0.02}
    """
    data = fetch_screener_data(symbol)
    return {
        "promoter" : data.get("promoter_holding"),
        "pledge"   : data.get("promoter_pledge"),
        "fii"      : data.get("fii_holding"),
        "dii"      : data.get("dii_holding"),
        "public"   : data.get("public_holding"),
    }


def get_10y_history(symbol: str) -> dict:
    """
    Returns 10-year historical series from screener.
    Keys: sales_10y, net_profit_10y, eps_10y, roe_10y, roce_10y
    """
    data = fetch_screener_data(symbol)
    return {
        "sales_10y"     : data.get("sales_10y", []),
        "net_profit_10y": data.get("net_profit_10y", []),
        "eps_10y"       : data.get("eps_10y", []),
        "roe_10y"       : data.get("roe_10y", []),
        "roce_10y"      : data.get("roce_10y", []),
    }


if __name__ == "__main__":
    # Quick test
    import json
    test_symbol = "INFY"
    print(f"\nFetching Screener.in data for {test_symbol}...\n")
    result = fetch_screener_data(test_symbol)
    print(json.dumps(result, indent=2, default=str))
