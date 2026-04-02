# =============================================================================
# config.py — India-Specific Valuation Defaults
# Stock Valuation Bot | valutionStock Project
# =============================================================================

# ── DISCOUNT RATES (WACC by market cap) ──────────────────────────────────────
DISCOUNT_RATE_LARGE_CAP  = 0.12   # 12% — Nifty 50 stocks
DISCOUNT_RATE_MID_CAP    = 0.14   # 14% — Nifty Midcap 100
DISCOUNT_RATE_SMALL_CAP  = 0.16   # 16% — Small caps / high risk

# ── GROWTH RATES ──────────────────────────────────────────────────────────────
TERMINAL_GROWTH_RATE     = 0.055  # 5.5% — India long-run GDP growth
DCF_STAGE2_GROWTH_FACTOR = 0.5    # Stage 2 (Yr 6-10) = 50% of Stage 1 growth
DCF_STAGE1_YEARS         = 5
DCF_STAGE2_YEARS         = 5

# ── INDIA MACRO ───────────────────────────────────────────────────────────────
GSEC_10Y_YIELD           = 0.07   # 7% — RBI 10-year G-Sec yield (update periodically)
EQUITY_RISK_PREMIUM      = 0.05   # 5% — India equity risk premium
GRAHAM_BASE_PE           = 8.5    # P/E of a zero-growth company (Graham)
GRAHAM_BOND_YIELD_BASE   = 4.4    # AAA bond yield when Graham wrote the formula

# ── OWNER EARNINGS ────────────────────────────────────────────────────────────
MAINTENANCE_CAPEX_RATIO  = 0.6    # 60% of reported Capex = maintenance capex

# ── EXCESS RETURNS MODEL (Banks / NBFCs) ──────────────────────────────────────
BETA_LARGE_BANK          = 1.1    # HDFC Bank, ICICI Bank typical beta
BETA_NBFC                = 1.3    # Bajaj Finance, Cholamandalam
# Cost of Equity = GSEC_10Y_YIELD + Beta × EQUITY_RISK_PREMIUM
# Example: 7% + 1.1 × 5% = 12.5%

# ── MARGIN OF SAFETY THRESHOLDS ───────────────────────────────────────────────
STRONG_BUY_THRESHOLD     = 0.30   # CMP is 30%+ below IV  → STRONG BUY
BUY_THRESHOLD            = 0.15   # CMP is 15-30% below IV → BUY
HOLD_UPPER               = 0.00   # CMP is 0-15% below IV  → HOLD
OVERVALUED_THRESHOLD     = 0.20   # CMP is 20%+ above IV   → OVERVALUED

# ── QUALITY FILTER MINIMUMS ───────────────────────────────────────────────────
MIN_ROE                  = 0.15   # 15% minimum ROE
MAX_DEBT_EQUITY          = 1.0    # Max D/E ratio (< 0.5 preferred)
MIN_REVENUE_GROWTH       = 0.10   # 10% minimum 5Y revenue CAGR
MIN_INTEREST_COVERAGE    = 3.0    # EBIT / Interest expense
MIN_CURRENT_RATIO        = 1.5    # Current Assets / Current Liabilities
MIN_GROSS_MARGIN         = 0.40   # 40% gross margin = moat proxy
MIN_FCF_POSITIVE_YEARS   = 3      # FCF positive in at least 3 of last 5 years

# ── CYCLICAL DETECTION ────────────────────────────────────────────────────────
CYCLICAL_REVENUE_STD_PCT = 0.20   # Revenue std dev > 20% flags as cyclical
CYCLICAL_LOOKBACK_YEARS  = 7      # Years to compute mid-cycle EBITDA

# ── EARLY STAGE DETECTION ─────────────────────────────────────────────────────
LOSS_MAKING_YEARS_THRESHOLD = 2   # Loss in 2 of last 3 years = early stage

# ── NSE TICKER SUFFIX ─────────────────────────────────────────────────────────
NSE_SUFFIX               = ".NS"  # Appended to all tickers for yfinance

# ── SECTOR LISTS (for auto-detection) ─────────────────────────────────────────
BANKING_SECTORS = [
    "Financial Services", "Banks", "Banking", "NBFC",
    "Diversified Financials", "Insurance"
]
PSU_KEYWORDS = [
    "Coal India", "ONGC", "NTPC", "Power Grid", "BHEL",
    "SAIL", "GAIL", "Oil India", "NMDC", "NALCO",
    "STATE BANK", "SBI", "PUNJAB NATIONAL BANK", "PNB",
    "BANK OF BARODA", "CANARA BANK", "UNION BANK",
    "INDIAN BANK", "UCO BANK"
]
IT_SECTORS = [
    "Technology", "Information Technology", "Software", "IT Services"
]
PHARMA_SECTORS = [
    "Healthcare", "Pharmaceutical", "Biotechnology", "Pharma"
]
CYCLICAL_SECTORS = [
    "Basic Materials", "Steel", "Metals", "Cement",
    "Chemicals", "Mining", "Aluminium"
]
FMCG_SECTORS = [
    "Consumer Defensive", "FMCG", "Consumer Staples"
]

# ── DISPLAY ───────────────────────────────────────────────────────────────────
CURRENCY_SYMBOL          = "₹"
REPORT_SEPARATOR         = "=" * 60
