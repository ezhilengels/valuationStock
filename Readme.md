# Stock Valuation Bot — Setup & Run Guide

## Step 1 — Install Python (if not installed)
Download Python 3.10+ from https://www.python.org/downloads/

## Step 2 — Install all required libraries
Open Terminal (Mac/Linux) or Command Prompt (Windows), navigate to
this folder and run:

```
pip install -r requirements.txt
```

---

## Option A — Terminal (Command Line)

### Single stock:
```
python main.py INFY
python main.py HDFCBANK
python main.py COALINDIA
```

### Multiple stocks with comparison table:
```
python main.py INFY HDFCBANK COALINDIA
```

### With Excel export:
```
python main.py INFY HDFCBANK --export
```

### Batch scan a preset watchlist:
```
python main.py --scan nifty50
python main.py --scan value_quality --filter buy
python main.py --scan banking --filter undervalued --export
```

### Show all available watchlists:
```
python main.py --lists
```

### Raw data only (debug):
```
python main.py RELIANCE --raw
```

---

## Option B — Web Dashboard (Streamlit) hhh

```
streamlit run dashboard.py
```

Then open your browser at: **http://localhost:8501**

### Dashboard Pages:
- **Single Stock Analysis** — Full report with charts and gauges
- **Batch Scanner** — Scan entire watchlists with live progress bar
- **Watchlist Manager** — View and manage all watchlists
- **About & Help** — Model explanations and command reference

### Dashboard Features:
- IV vs CMP bar chart (all models side by side)
- Margin of Safety gauge (colour-coded)
- Quality scorecard with pass/fail indicators
- Buffett earnings yield vs G-Sec comparison
- Relative valuation table with colour coding
- Batch scan with pie chart verdict distribution
- One-click Excel download from the browser

---

## Project Structure (27 files)
```
valutionStock/
├── main.py              ← Terminal entry point
├── dashboard.py         ← Web dashboard (Streamlit)
├── config.py            ← All settings and thresholds
├── requirements.txt
│
├── data/
│   ├── fetcher.py       ← Live NSE data via yfinance
│   └── cleaner.py       ← Missing value handler
│
├── screening/
│   ├── detector.py      ← Auto stock type classification
│   ├── quality_filter.py← Buffett quality checklist
│   ├── scanner.py       ← Batch scan engine
│   └── watchlists.py    ← 10 preset NSE watchlists
│
├── valuation/
│   ├── graham.py        ← Benjamin Graham (simple + adjusted)
│   ├── dcf.py           ← 2-stage Discounted Cash Flow
│   ├── lynch.py         ← Peter Lynch PEG method
│   ├── buffett.py       ← Owner Earnings + Earnings Yield
│   ├── epv.py           ← Earnings Power Value (Greenwald)
│   ├── ddm.py           ← Dividend Discount Model
│   ├── excess_returns.py← Excess Returns (Banks/NBFCs)
│   ├── ev_sales.py      ← EV/Sales (Early-stage stocks)
│   ├── mid_cycle.py     ← Mid-Cycle EV/EBITDA (Cyclicals)
│   └── relative.py      ← Peer comparison valuation
│
├── verdict/
│   ├── aggregator.py    ← Weighted IV calculator
│   └── decision.py      ← BUY/HOLD/OVERVALUED engine
│
└── output/
    ├── report.py        ← Coloured terminal report
    └── export.py        ← 4-sheet Excel report
```

## Watchlists Available
| Name | Stocks | Focus |
|---|---|---|
| nifty50 | 50 | Nifty 50 large caps |
| niftynext50 | 50 | Nifty Next 50 |
| midcap50 | 50 | Midcap 50 |
| value_quality | 25 | Buffett-style quality picks |
| psu_dividend | 15 | PSU dividend plays |
| banking | 15 | Banks & NBFCs |
| it_tech | 15 | IT & Software |
| pharma | 15 | Pharma & Healthcare |
| cyclicals | 15 | Steel, Cement, Metals |
| custom | varies | Your personal list |

## Troubleshooting
- `ModuleNotFoundError` → Run `pip install -r requirements.txt`
- `No data found` → Check ticker spelling (use NSE symbol, e.g. HDFCBANK)
- `Data gaps` → Some fields default to estimates (shown in terminal output)
- Streamlit not opening → Check http://localhost:8501 in browser
