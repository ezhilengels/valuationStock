# Python Stock Valuation Bot — Complete Build Plan
### For NSE Indian Stocks | Fair Value + Discount Scanner

---

## OVERVIEW

A Python bot that takes any NSE stock ticker, fetches live financial data, runs all major valuation models, compares intrinsic value against CMP, and delivers a clear **BUY / HOLD / OVERVALUED** verdict. This is the same multi-model framework used by top Indian mutual funds, FIIs, and institutional desks.

---

## PART 1 — PROJECT ARCHITECTURE

```
stock_valuation_bot/
│
├── main.py                  ← Entry point, CLI interface
├── config.py                ← Settings: discount rate, growth assumptions, G-Sec yield
│
├── data/
│   ├── fetcher.py           ← Fetch live data from yfinance / screener.in / NSE API
│   ├── cleaner.py           ← Normalize, clean, handle missing values
│   └── cache.py             ← Cache API responses (avoid rate limits)
│
├── valuation/
│   ├── graham.py            ← Benjamin Graham formula (original + updated)
│   ├── dcf.py               ← Discounted Cash Flow (2-stage)
│   ├── lynch.py             ← Peter Lynch PEG fair value
│   ├── buffett.py           ← Owner Earnings / Earnings Yield method
│   ├── epv.py               ← Earnings Power Value (Greenwald)
│   ├── ddm.py               ← Dividend Discount Model
│   ├── excess_returns.py    ← Excess Returns Model for Banks/NBFCs
│   ├── ev_sales.py          ← EV/Sales for early-stage/loss-making stocks
│   ├── mid_cycle.py         ← Mid-cycle EV/EBITDA for cyclicals
│   └── relative.py          ← P/E, EV/EBITDA, P/B, PEG peer comparison
│
├── screening/
│   ├── quality_filter.py    ← ROE > 15%, D/E < 1, Revenue growth > 10%
│   ├── buffett_checklist.py ← Moat proxy, ROE consistency, debt check
│   ├── detector.py          ← Auto-detect stock type (BANK/CYCLICAL/GROWTH etc.)
│   └── scanner.py           ← Batch scan multiple stocks
│
├── verdict/
│   ├── aggregator.py        ← Combine all model outputs into single score
│   └── decision.py          ← BUY / HOLD / OVERVALUED logic
│
├── output/
│   ├── report.py            ← Pretty terminal output + colour coding
│   └── export.py            ← Save to Excel / CSV / JSON
│
└── requirements.txt
```

---

## PART 2 — DATA SOURCES (What to Fetch)

### Primary Data Points Needed

| Data Point | Used In |
|---|---|
| EPS (TTM) | Graham, Lynch, Buffett Earnings Yield |
| EPS Growth Rate (5Y) | Graham, PEG |
| Free Cash Flow | DCF |
| Net Profit | DCF, Owner Earnings |
| Depreciation | Owner Earnings |
| Capex | Owner Earnings, DCF |
| EBIT | EPV |
| Revenue | Quality filter, EV/EBITDA |
| Book Value per share | P/B |
| Dividend (DPS) | DDM |
| Dividend Growth Rate | DDM |
| Total Debt | D/E ratio, EV |
| Cash & Equivalents | EV calculation |
| Shares Outstanding | EV, per-share values |
| Market Cap | CMP cross-check |
| CMP (live price) | Comparison with all IVs |
| ROE (3Y / 5Y) | Buffett checklist, quality filter |
| Debt/Equity | Quality filter |
| Tax Rate | EPV |
| EBITDA | EV/EBITDA |
| G-Sec 10Y yield | Graham updated, Earnings Yield comparison |

### Data Source Libraries

```python
# Primary: yfinance (free, works for NSE)
import yfinance as yf
ticker = yf.Ticker("INFY.NS")   # Note: .NS suffix for NSE stocks

# Secondary: NSEpy (for historical NSE data)
# pip install nsetools nsepy

# Tertiary: Screener.in scraping (for Indian-specific ratios)
# requests + BeautifulSoup for structured scraping

# G-Sec yield: RBI API or hardcode as config default (7%)
```

---

## PART 3 — VALUATION MODULE DETAILS

### Module 1: Benjamin Graham Formula

```
graham.py

Formula A (Original 1962):
  IV = EPS × (8.5 + 2g)

  Where:
    EPS = Trailing 12 month EPS
    g   = Expected EPS growth rate % (5-7 year estimate)
    8.5 = Base P/E for zero-growth company

Formula B (Updated 1974 — Interest Rate Adjusted):
  IV = EPS × (8.5 + 2g) × (4.4 / Y)

  Where:
    Y   = Current 10-year G-Sec yield (India: ~7%)
    4.4 = AAA bond yield when Graham wrote this

Output: Graham IV (simple) + Graham IV (adjusted)
```

### Module 2: DCF — Discounted Cash Flow

```
dcf.py

2-Stage DCF for Indian Stocks:

Stage 1 (Years 1–5):
  FCF grows at high_growth_rate (analyst estimate or 5Y average)

Stage 2 (Years 6–10):
  FCF grows at moderate_rate = high_growth_rate / 2

Terminal Value (Year 10+):
  TV = FCF_year10 × (1 + terminal_g) / (discount_rate − terminal_g)
  terminal_g = 5.5% (India long-run GDP growth)

Discount Rate = WACC:
  Default: 12% for large cap, 14% for mid/small cap

Present Value:
  PV = Σ [FCFt / (1 + r)^t] + TV / (1 + r)^10

Per Share IV = Total PV / Shares Outstanding

Inputs needed:
  - FCF (last 3 years, use average)
  - High growth rate (use 5Y EPS CAGR as proxy)
  - Shares outstanding
```

### Module 3: Peter Lynch PEG Method

```
lynch.py

Fair Value P/E = EPS Growth Rate %
Fair Value IV  = EPS × EPS Growth Rate

PEG Ratio = (P/E) / EPS Growth Rate
  PEG < 1   → Undervalued
  PEG 1-2   → Fairly Valued
  PEG > 2   → Overvalued

Output: Fair Price, PEG ratio, PEG verdict
```

### Module 4: Warren Buffett Owner Earnings

```
buffett.py

Owner Earnings = Net Profit + Depreciation − Maintenance Capex

  Maintenance Capex ≈ Total Capex × 0.6 (rule of thumb)
  OR use: Capex if Capex < Depreciation, else Depreciation

Intrinsic Value = Owner Earnings / (r − g)
  r = 12% (required return for India)
  g = sustainable long-term growth (use 6%)
  Multiplier = 1 / (0.12 − 0.06) = 16.67

Per Share IV = Total IV / Shares Outstanding

Also compute Earnings Yield:
  Earnings Yield = EPS / CMP × 100
  Compare vs G-Sec yield (7%)
  If EY > G-Sec → stock more attractive than bonds
```

### Module 5: Earnings Power Value (EPV)

```
epv.py

EPV = Adjusted EBIT × (1 − Tax Rate) / WACC

  Adjusted EBIT = Average EBIT (3-year) — remove one-time items
  Tax Rate = Effective tax rate from financials
  WACC = 12% default (India large cap)

This assumes ZERO growth — pure earning power today.
If CMP < EPV → cheap even with no growth assumptions.

Per Share EPV = Total EPV / Shares Outstanding
```

### Module 6: Dividend Discount Model (DDM)

```
ddm.py

Gordon Growth Model:
  IV = D1 / (r − g)

  D1  = Expected dividend next year = DPS × (1 + g)
  DPS = Dividend per share (last year)
  r   = Required return = 12%
  g   = Dividend growth rate (5Y CAGR of dividends)

Conditions for reliability:
  - Only use if dividend yield > 1%
  - Only use for companies with consistent 5+ year dividend history
  - Skip for growth companies with zero/minimal dividends

Flag if r <= g (model breaks down)
```

### Module 7: Relative Valuation

```
relative.py

Metrics computed:
  1. P/E ratio vs 5Y historical average P/E
  2. EV/EBITDA vs sector median
  3. P/B ratio (critical for banks/NBFCs)
  4. PEG ratio
  5. EV = Market Cap + Total Debt − Cash

Peer comparison logic:
  - Fetch sector/industry from yfinance
  - Compare key multiples vs sector median
  - Flag if stock is 20%+ cheaper than peers (potential value)
  - Flag if stock is 30%+ more expensive (potential overvaluation)
```

---

## PART 4 — QUALITY FILTER (Buffett's Checklist)

```
quality_filter.py  +  buffett_checklist.py

Must-pass filters before valuation is even run:

PROFITABILITY:
  ✓ ROE > 15% (consistent over 3 years)
  ✓ Net Profit Margin > 10% (for non-financials)
  ✓ Operating Cash Flow > Net Profit (quality of earnings check)

SAFETY:
  ✓ Debt/Equity < 1.0 (< 0.5 preferred)
  ✓ Interest Coverage Ratio > 3x
  ✓ Current Ratio > 1.5

GROWTH:
  ✓ Revenue CAGR > 10% (5 year)
  ✓ EPS CAGR > 10% (5 year)
  ✓ Positive FCF for at least 3 of last 5 years

MOAT PROXIES (Buffett's key question):
  ✓ Gross Margin > 40% → pricing power
  ✓ ROE consistently > 15% over 5 years → competitive advantage
  ✓ Low capex vs revenue (asset-light model) → scalability

Output: PASS / PARTIAL / FAIL with specific reasons
```

---

## PART 5 — VERDICT AGGREGATION ENGINE

```
aggregator.py  +  decision.py

Step 1 — Collect all intrinsic values:
  IV_graham_simple
  IV_graham_adjusted
  IV_dcf
  IV_lynch
  IV_buffett_owner_earnings
  IV_epv
  IV_ddm (only if dividend stock)

Step 2 — Weighted Average IV (by stock type from detector.py):

  LARGE_STABLE (ITC, HUL):
    DCF 40% + DDM 30% + Graham 30%

  HIGH_GROWTH (IT, Pharma):
    DCF 60% + PEG/Lynch 40%
    Skip: DDM, EPV

  BANK_NBFC (HDFC Bank, Bajaj Finance):
    Excess Returns Model 60% + EPV 40%
    Skip: DCF, EV/EBITDA, Owner Earnings

  PSU (Coal India, ONGC, NTPC):
    DDM 50% + EV/EBITDA 50%
    Skip: DCF, PEG

  EARLY_STAGE (Zomato, Paytm):
    EV/Sales 50% + Price/TAM 50%
    Skip: ALL earnings-based formulas → bot flags warning

  CYCLICAL (Steel, Cement):
    Mid-Cycle EV/EBITDA 70% + P/B floor check 30%
    NEVER use current P/E → bot blocks this automatically

  GENERAL (everything else):
    DCF 35% + Graham 25% + Lynch 20% + EPV 20%

Step 3 — Margin of Safety check:
  Discount to IV = (IV − CMP) / IV × 100

  > 30% below IV   → STRONG BUY
  15-30% below IV  → BUY
  0-15% below IV   → FAIRLY VALUED / HOLD
  0-20% above IV   → SLIGHTLY OVERVALUED
  > 20% above IV   → OVERVALUED / AVOID

Step 4 — Quality Gate:
  If Quality Filter = FAIL → override to AVOID regardless of IV

Step 5 — Relative Valuation Gate:
  If stock is expensive vs ALL peers AND overvalued → AVOID
  If stock is cheap vs peers AND undervalued → upgrade to STRONG BUY

Final Output:
  STRONG BUY | BUY | HOLD | OVERVALUED | AVOID
```

---

## PART 6 — BATCH SCANNER MODULE

```
scanner.py

Purpose: Scan a watchlist of stocks at once

Features:
  - Input: list of NSE tickers (from CSV or hardcoded list)
  - Run full valuation on each
  - Filter: show only BUY and STRONG BUY
  - Sort by: Discount to IV (highest discount first)
  - Export: results to Excel with colour coding

Preset watchlists to include:
  - Nifty 50 stocks
  - Nifty Next 50
  - Nifty Midcap 100
  - Custom user watchlist

Rate limiting: 1-2 second delay between API calls to avoid blocks
```

---

## PART 7 — OUTPUT & REPORTING

### Terminal Output (Coloured)

```
=============================================
  STOCK VALUATION REPORT — INFY.NS
  Infosys Ltd | IT Sector
  As of: 2 Apr 2026
=============================================

CMP: ₹1,842

--- QUALITY GATE ---
  ROE (3Y avg):        22.4%   ✓ PASS
  Debt/Equity:          0.08   ✓ PASS
  Revenue CAGR 5Y:     12.3%   ✓ PASS
  FCF Positive Years:   5/5    ✓ PASS
  Quality Score:       STRONG PASS

--- INTRINSIC VALUE ESTIMATES ---
  Graham (Simple):     ₹2,100
  Graham (Adjusted):   ₹1,980
  DCF (2-stage):       ₹2,350
  Peter Lynch:         ₹2,040
  Owner Earnings:      ₹2,150
  EPV:                 ₹1,790
  DDM:                  N/A (growth stock)

  Weighted IV:         ₹2,130

--- MARGIN OF SAFETY ---
  Discount to IV:      13.5%
  Verdict:             FAIRLY VALUED / HOLD

--- RELATIVE VALUATION ---
  P/E:     24x   (Sector avg: 26x)  → Slight discount
  EV/EBITDA: 18x (Sector avg: 19x) → In line
  PEG:      1.6  → Fair

--- EARNINGS YIELD vs G-SEC ---
  Earnings Yield:    6.8%
  G-Sec 10Y:         7.0%
  → Bonds marginally better at current price

--- FINAL VERDICT ---
  ⭐ HOLD — Fair valued, wait for 15-20% correction
=============================================
```

### Excel Export Columns

| Ticker | CMP | IV (Graham) | IV (DCF) | IV (Lynch) | IV (Owner Earnings) | IV (EPV) | Weighted IV | Discount % | Quality | Verdict |

---

## PART 8 — TECHNOLOGY STACK

```
Language:    Python 3.10+

Libraries:
  yfinance        — Live NSE stock data
  pandas          — Data handling, calculations
  numpy           — Mathematical operations
  requests        — Web scraping for missing data
  beautifulsoup4  — Parse screener.in if needed
  openpyxl        — Export to Excel
  colorama        — Terminal colour output
  tabulate        — Formatted terminal tables
  tqdm            — Progress bar for batch scanner

Optional (for dashboard later):
  streamlit       — Web dashboard UI
  plotly          — Charts and graphs

Install command:
  pip install yfinance pandas numpy requests beautifulsoup4 \
              openpyxl colorama tabulate tqdm streamlit plotly
```

---

## PART 9 — BUILD ORDER (Step-by-Step)

### Phase 1 — Foundation (Week 1)
1. Set up project folder structure
2. Build `config.py` with all default assumptions
3. Build `data/fetcher.py` — fetch and display raw financial data for one ticker
4. Test data fetching on 5 different stocks (INFY, HDFC Bank, ITC, Titan, Coal India)
5. Build `data/cleaner.py` — handle missing values, wrong data types

### Phase 2 — Valuation Modules (Week 2)
6.  Build and test `graham.py` first (simplest)
7.  Build and test `lynch.py`
8.  Build and test `buffett.py` (Owner Earnings + Earnings Yield)
9.  Build and test `epv.py`
10. Build and test `ddm.py`
11. Build and test `dcf.py` (most complex — save for last in this phase)
12. Build and test `excess_returns.py` — Banks/NBFCs (ROE vs Cost of Equity)
13. Build and test `ev_sales.py` — Early stage / loss-making stocks
14. Build and test `mid_cycle.py` — Cyclicals using 7-10 year avg EBITDA

### Phase 3 — Filters, Detection & Verdict (Week 3)
15. Build `quality_filter.py`
16. Build `buffett_checklist.py`
17. Build `detector.py` — auto-detect stock type from sector + financials
18. Build `relative.py` (peer comparison)
19. Build `aggregator.py` — weighted IV using stock-type-aware weights
20. Build `decision.py` — BUY/HOLD/OVERVALUED logic

### Phase 4 — Output & Polish (Week 4)
17. Build `report.py` — formatted terminal output with colours
18. Build `export.py` — Excel report generation
19. Build `scanner.py` — batch scan mode
20. Build `main.py` — CLI with argument parsing (single stock or batch scan)
21. End-to-end testing on 20 stocks across sectors
22. Fine-tune weights in aggregator based on results

### Phase 5 — Dashboard (Optional, Week 5+)
23. Build Streamlit web UI
24. Add sector comparison charts
25. Add historical P/E trend chart per stock
26. Add watchlist management

---

## PART 10 — CONFIG DEFAULTS (India-Specific)

```python
# config.py

# Discount Rates
DISCOUNT_RATE_LARGE_CAP   = 0.12   # 12%
DISCOUNT_RATE_MID_CAP     = 0.14   # 14%
DISCOUNT_RATE_SMALL_CAP   = 0.16   # 16%

# Terminal Growth Rate
TERMINAL_GROWTH_RATE      = 0.055  # 5.5% (India long-run GDP)

# G-Sec Yield (update periodically)
GSEC_10Y_YIELD            = 0.07   # 7%

# Graham Base P/E
GRAHAM_BASE_PE            = 8.5
GRAHAM_BOND_YIELD_BASE    = 4.4    # When Graham wrote formula

# Margin of Safety Thresholds
STRONG_BUY_THRESHOLD      = 0.30   # 30%+ below IV
BUY_THRESHOLD             = 0.15   # 15-30% below IV
HOLD_THRESHOLD            = 0.00   # 0-15% below IV
OVERVALUED_THRESHOLD      = 0.20   # 20%+ above IV

# Quality Filters
MIN_ROE                   = 0.15   # 15%
MAX_DEBT_EQUITY           = 1.0
MIN_REVENUE_GROWTH        = 0.10   # 10%
MIN_INTEREST_COVERAGE     = 3.0

# DCF Stages
DCF_STAGE1_YEARS          = 5
DCF_STAGE2_YEARS          = 5      # Years 6-10
DCF_STAGE2_GROWTH_FACTOR  = 0.5   # Half of stage 1 growth

# Owner Earnings
MAINTENANCE_CAPEX_RATIO   = 0.6   # 60% of total capex
```

---

## PART 11 — KNOWN CHALLENGES & SOLUTIONS

| Challenge | Solution |
|---|---|
| yfinance data gaps for small NSE stocks | Fallback to screener.in scraping |
| Negative FCF in early-stage companies | Skip DCF, flag in report, use EV/Sales instead |
| Banks/NBFCs have no EV/EBITDA | Auto-detect financials, use P/B + ROA model |
| EPS growth estimates not available | Use 5Y historical EPS CAGR as proxy |
| API rate limits | Add cache layer + time.sleep(1.5) between calls |
| Currency/split adjustments | Use yfinance auto-adjusted prices |
| PSU companies with irregular dividends | Use 3Y average dividend for DDM |

---

## PART 12 — WHICH FORMULA FOR WHICH STOCK (Complete Mapping)

This is the core intelligence of the bot. Auto-detect stock type from
sector/financials and apply the right models with the right weights.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOCK TYPE MAP — What the bot uses for each category
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. LARGE STABLE COMPANIES (ITC, HUL, Nestlé, Asian Paints)
   Primary  : DCF (40%) + DDM (30%) + Graham (30%)
   Logic    : Predictable cash flows, consistent dividends,
              strong moat — all 3 models work well here
   Skip     : PEG (slow growth, Lynch formula overpunishes)
   Signal   : Moat check must PASS before valuation runs

2. HIGH GROWTH IT / PHARMA (Infosys, TCS, Dr Reddy's, Divis)
   Primary  : PEG — Peter Lynch (40%) + 2-Stage DCF (60%)
   Logic    : Earnings growth is the key driver
              PEG < 1 at current CMP = strong signal
   Skip     : DDM (minimal dividends), EPV (understates growth)
   Special  : For Pharma — adjust DCF for pipeline uncertainty
              (use conservative Stage 1 growth = 60% of reported)

3. BANKS AND NBFCs (HDFC Bank, ICICI, Bajaj Finance, Kotak)
   Primary  : P/B Ratio + Excess Returns Model (60%) + EPV (40%)
   Logic    : Book value is the anchor for financial companies
              EV/EBITDA is meaningless for banks (interest is revenue)
   Excess Returns Model:
     Value = Book Value + PV of (ROE − Cost of Equity) × Book Value
     Cost of Equity = Risk-free rate + Beta × Equity Risk Premium
     = 7% + 1.1 × 5% = 12.5% (typical India large bank)
     If ROE > CoE → stock deserves premium to book
     If ROE < CoE → stock deserves discount to book
   Skip     : DCF, EV/EBITDA, Owner Earnings (FCF not meaningful)
   Benchmark: HDFC Bank ROE ~17% > CoE 12.5% → justified premium P/B

4. PSUs — Coal India, ONGC, NTPC, Power Grid, BHEL
   Primary  : DDM (50%) + EV/EBITDA (50%)
   Logic    : PSUs pay high dividends regularly — DDM is reliable
              EV/EBITDA normalises debt and tax differences
   DDM Note : Use 3-year average dividend (PSU payouts are policy-driven,
              can be irregular year to year)
   Skip     : DCF (capex-heavy, FCF distorted), PEG (low growth)
   Special  : For commodity PSUs use mid-cycle EBITDA, not peak/trough

5. EARLY STAGE / LOSS-MAKING (Zomato, Paytm, Nykaa, PolicyBazaar)
   Primary  : EV/Sales (50%) + Price/TAM (50%)
   Logic    : No earnings, no dividends → traditional formulas BREAK
              Value = market share × total addressable market × margin potential
   EV/Sales : Compare vs global peers in same sector
              Zomato → compare vs DoorDash, Delivery Hero EV/Sales
   Price/TAM: Rough check: if Market Cap < 5% of TAM → room to grow
   Skip     : ALL earnings-based formulas (Graham, DCF, Lynch, EPV, DDM)
   Warning  : Bot will flag "EARNINGS-BASED VALUATION NOT APPLICABLE"
              and switch to EV/Sales mode automatically
   Detection: If Net Profit < 0 for 2 of last 3 years → early stage mode

6. CYCLICALS — Steel, Cement, Aluminium, Chemicals (Tata Steel, UltraTech)
   Primary  : EV/EBITDA at MID-CYCLE earnings (100%)
   Logic    : Earnings swing wildly — peak earnings overvalue,
              trough earnings undervalue → must use normalised mid-cycle
   Mid-Cycle EBITDA = Average EBITDA over last full business cycle (7-10 years)
   NEVER use: Current-year EPS or P/E for cyclicals (extremely misleading)
   Example  : Steel company at peak cycle P/E = 5x looks cheap but is EXPENSIVE
              Same company at mid-cycle EV/EBITDA = 8x is the right measure
   Secondary: P/B as floor value check (asset-heavy businesses)
   Detection: Revenue standard deviation > 20% over 5 years → cyclical flag

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADDITIONAL SECTORS (Secondary mapping)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IT / Software:
  Primary: DCF + PEG | Skip: DDM, P/B

FMCG / Consumer Staples:
  Primary: DCF + Graham | Strong moat check required

Pharma / Healthcare:
  Primary: PEG + DCF | Haircut Stage 1 growth for pipeline risk

Infrastructure / Capital Goods:
  Primary: EV/EBITDA + DCF | Use higher WACC 14%

Telecom / Utilities:
  Primary: EV/EBITDA + DDM | Asset-heavy, regulated returns

Real Estate (REITs):
  Primary: NAV (Net Asset Value) + Dividend Yield
  NAV = Market value of all properties − Total debt / Shares

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUTO-DETECTION LOGIC IN CODE (detector.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_stock_type(ticker_data):
  if net_profit < 0 for 2/3 years:
      return "EARLY_STAGE"
  if sector in ["Banking", "Financial Services", "NBFC"]:
      return "BANK_NBFC"
  if sector in ["Oil & Gas", "Power", "Mining"] and govt_owned:
      return "PSU"
  if revenue_std_dev_pct > 20%:
      return "CYCLICAL"
  if eps_growth > 20% and sector in ["IT", "Pharma"]:
      return "HIGH_GROWTH"
  if dividend_yield > 2% and eps_growth < 12%:
      return "LARGE_STABLE"
  else:
      return "GENERAL"   ← runs all 6 models with equal weight
```

---

## SUMMARY — WHAT THIS BOT WILL DO

1. **Input**: Any NSE ticker (e.g., `RELIANCE`, `INFY`, `HDFCBANK`)
2. **Fetch**: All required financial data automatically
3. **Quality Gate**: Check if stock passes Buffett's quality checklist
4. **9 Valuation Models**: Graham, DCF, Lynch, Owner Earnings, EPV, DDM, Excess Returns (Banks), EV/Sales (Early-stage), Mid-Cycle EV/EBITDA (Cyclicals)
5. **Relative Valuation**: Compare vs peers and historical averages
6. **Weighted Verdict**: Combine all models → single intrinsic value
7. **Margin of Safety**: Calculate discount/premium to CMP
8. **Decision**: STRONG BUY / BUY / HOLD / OVERVALUED / AVOID
9. **Report**: Clean terminal output + Excel export
10. **Batch Mode**: Scan 50-500 stocks, filter only undervalued ones

---

*Plan Version 1.1 | April 2026 | valutionStock Project*
*Updated: Added Excess Returns model (Banks), EV/Sales (Early-stage), Mid-Cycle EV/EBITDA (Cyclicals), detector.py auto-classification*
