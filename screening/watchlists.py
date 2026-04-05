# =============================================================================
# screening/watchlists.py — Preset NSE Stock Watchlists
#
# Usage:
#   from screening.watchlists import get_watchlist
#   tickers = get_watchlist("nifty50")
# =============================================================================


WATCHLISTS = {

    # ── Nifty 50 ─────────────────────────────────────────────────────────────
    "nifty50": [
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
        "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BPCL", "BHARTIARTL",
        "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
        "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE",
        "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC",
        "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT",
        "LTIM", "M&M", "MARUTI", "NESTLEIND", "NTPC",
        "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
        "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
        "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
    ],

    # ── Nifty Next 50 ────────────────────────────────────────────────────────
    "niftynext50": [
        "ABB", "ADANIGREEN", "ADANITRANS", "AMBUJACEM", "BAJAJHLDNG",
        "BANKBARODA", "BERGEPAINT", "BEL", "BOSCHLTD", "CANBK",
        "CHOLAFIN", "COLPAL", "DLF", "DMART", "GODREJCP",
        "GAIL", "HAVELLS", "HAL", "ICICIGI", "ICICIPRULI",
        "INDUSTOWER", "IOC", "IRCTC", "JINDALSTEL", "LICI",
        "MARICO", "MCDOWELL-N", "MUTHOOTFIN", "NAUKRI", "NHPC",
        "NMDC", "OFSS", "PAGEIND", "PIDILITIND", "PFC",
        "PIIND", "RECLTD", "SAIL", "SHREECEM", "SIEMENS",
        "SOLARINDS", "SRF", "TATAPOWER", "TORNTPHARM", "TVSMOTOR",
        "UBL", "VEDL", "VOLTAS", "WHIRLPOOL", "ZYDUSLIFE",
    ],

    # ── Nifty Midcap 50 (curated) ─────────────────────────────────────────────
    "midcap50": [
        "ABBOTINDIA", "ABCAPITAL", "ALKEM", "APOLLOTYRE", "ASTRAL",
        "AUROPHARMA", "BALKRISIND", "BATAINDIA", "BIOCON", "CAMS",
        "CANFINHOME", "COFORGE", "CROMPTON", "CUMMINSIND", "DABUR",
        "DEEPAKNITR", "DIXON", "ELGIEQUIP", "EMAMILTD", "ESCORTS",
        "EXIDEIND", "FEDERALBNK", "GLENMARK", "GODREJIND", "GRANULES",
        "HDFCAMC", "IDFCFIRSTB", "IPCALAB", "JBCHEPHARM", "KANSAINER",
        "LALPATHLAB", "LUPIN", "METROPOLIS", "MFSL", "MOTHERSON",
        "MPHASIS", "NATCOPHARM", "OBEROIRLTY", "PERSISTENT", "PFIZER",
        "POLYCAB", "RBLBANK", "RELAXO", "SCHAEFFLER", "SUPREMEIND",
        "TATACOMM", "TORNTPOWER", "TTKPRESTIG", "VGUARD", "ZEEL",
    ],

    # ── Nifty Midcap 100 (extended — adds 50 more mid caps) ──────────────────
    "midcap100": [
        # Existing midcap50 base
        "ABBOTINDIA", "ABCAPITAL", "ALKEM", "APOLLOTYRE", "ASTRAL",
        "AUROPHARMA", "BALKRISIND", "BATAINDIA", "BIOCON", "CAMS",
        "CANFINHOME", "COFORGE", "CROMPTON", "CUMMINSIND", "DABUR",
        "DEEPAKNITR", "DIXON", "ELGIEQUIP", "EMAMILTD", "ESCORTS",
        "EXIDEIND", "FEDERALBNK", "GLENMARK", "GODREJIND", "GRANULES",
        "HDFCAMC", "IDFCFIRSTB", "IPCALAB", "JBCHEPHARM", "KANSAINER",
        "LALPATHLAB", "LUPIN", "METROPOLIS", "MFSL", "MOTHERSON",
        "MPHASIS", "NATCOPHARM", "OBEROIRLTY", "PERSISTENT", "PFIZER",
        "POLYCAB", "RBLBANK", "RELAXO", "SCHAEFFLER", "SUPREMEIND",
        "TATACOMM", "TORNTPOWER", "TTKPRESTIG", "VGUARD", "ZEEL",
        # Additional midcap 51–100
        "AAVAS", "ABFRL", "AIAENG", "AJANTPHARM", "ANGELONE",
        "ASHOKLEY", "ATGL", "ATUL", "BASF", "BFDL",
        "BLUESTARCO", "CAMPUS", "CERA", "COROMANDEL", "CRAFTSMAN",
        "DALBHARAT", "DATAPATTNS", "DELTACORP", "ERIS", "FLUOROCHEM",
        "GESHIP", "GNFC", "GRINDWELL", "HAPPSTMNDS", "HATSUN",
        "IDBI", "IGPL", "IIFL", "INDIAMART", "IRFC",
        "JKLAKSHMI", "JKPAPER", "JSWENERGY", "KAJARIACER", "KESORAMIND",
        "KIMS", "KNR", "KROMARETAIL", "LAURUSLABS", "LXCHEM",
        "MANAPPURAM", "MAZDOCK", "MRPL", "NOCIL", "NUVAMA",
        "OLECTRA", "ORIENTELEC", "PNBHOUSING", "PRESTIGE", "ROUTE",
    ],

    # ── REITs & InvITs ───────────────────────────────────────────────────────
    "reits_invits": [
        # REITs (office)
        "EMBASSY",       # Embassy Office Parks REIT
        "MINDSPACE",     # Mindspace Business Parks REIT
        "BIRET",         # Brookfield India Real Estate Trust
        "NEXUS",         # Nexus Select Trust (retail REIT)
        # InvITs (infrastructure)
        "IRBINVIT",      # IRB Infrastructure Developers InvIT
        "INDIGRID",      # India Grid Trust InvIT
        "POWERGRID",     # PowerGrid Infrastructure InvIT
        "NHAI",          # NHAI InvIT
    ],

    # ── Quality / Value Focus (Buffett-style screen) ──────────────────────────
    "value_quality": [
        "ASIANPAINT", "BRITANNIA", "COLPAL", "DABUR", "HINDUNILVR",
        "ITC", "MARICO", "NESTLEIND", "PIDILITIND", "TATACONSUM",
        "TITAN", "BAJFINANCE", "HDFCBANK", "ICICIBANK", "KOTAKBANK",
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM",
        "SUNPHARMA", "DIVISLAB", "DRREDDY", "CIPLA", "APOLLOHOSP",
    ],

    # ── PSU Focus (dividend / value plays) ────────────────────────────────────
    "psu_dividend": [
        "COALINDIA", "ONGC", "POWERGRID", "NTPC", "SBIN",
        "BANKBARODA", "CANBK", "IOC", "BPCL", "GAIL",
        "NHPC", "NMDC", "SAIL", "PFC", "RECLTD",
    ],

    # ── Banking & Finance ─────────────────────────────────────────────────────
    "banking": [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK",
        "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "RBLBANK",
        "BAJFINANCE", "BAJAJFINSV", "CHOLAFIN", "MUTHOOTFIN", "LICHSGFIN",
    ],

    # ── IT & Technology ───────────────────────────────────────────────────────
    "it_tech": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM",
        "TECHM", "MPHASIS", "COFORGE", "PERSISTENT", "OFSS",
        "KPITTECH", "TATAELXSI", "MASTEK", "NIITTECH", "HEXAWARE",
    ],

    # ── Pharma & Healthcare ───────────────────────────────────────────────────
    "pharma": [
        "SUNPHARMA", "DIVISLAB", "DRREDDY", "CIPLA", "APOLLOHOSP",
        "LUPIN", "AUROPHARMA", "TORNTPHARM", "ALKEM", "IPCA",
        "GLENMARK", "BIOCON", "NATCOPHARM", "GRANULES", "JBCHEPHARM",
    ],

    # ── Cyclicals (Steel / Cement / Metals) ───────────────────────────────────
    "cyclicals": [
        "TATASTEEL", "JSWSTEEL", "SAIL", "HINDALCO", "VEDL",
        "NMDC", "NATIONALUM", "JINDALSTEL", "RATNAMANI", "APL",
        "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "RAMCOCEM",
    ],

    # ── Small / Custom Watchlist (edit as needed) ────────────────────────────
    "custom": [
        "INFY", "HDFCBANK", "COALINDIA",
    ],
     # ── 8 SECTORAL BUCKETS (NSE STANDARD) ───────────────────────────────────
    "financials_v2": [
        "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", 
        "BAJFINANCE", "CHOLAFIN", "RECLTD", "PFC", "HDFCLIFE", "SBILIFE",
        "MUTHOOTFIN"
    ],

    "technology_v2": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "PERSISTENT", "COFORGE"
    ],

    "consumer_v2": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", 
        "VBL", "TITAN", "ASIANPAINT", "BERGEPAINT", "HAVELLS", "TRENT"
    ],

    "healthcare_v2": [
        "SUNPHARMA", "CIPLA", "DRREDDY", "DIVISLAB", "APOLLOHOSP", 
        "MAXHEALTH", "MANKIND", "TORNTPHARM"
    ],

    "automobile_v2": [
        "TATAMOTORS", "M&M", "MARUTI", "BAJAJ-AUTO", "EICHERMOT", 
        "TVSMOTOR", "HEROMOTOCO", "SONACOMS"
    ],

    "energy_v2": [
        "RELIANCE", "ONGC", "COALINDIA", "BPCL", "NTPC", 
        "POWERGRID", "ADANIGREEN", "TATAPOWER"
    ],

    "materials_v2": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "JINDALSTEL", 
        "ULTRACEMCO", "GRASIM", "PIDILITIND", "SRF"
    ],

    "chemicals_v2": [
        "SRF", "DEEPAKNITR", "TATACHEM", "NAVINFLUOR", "AARTIIND", "GUJGASLTD"
    ],

    "infrastructure_v2": [
        "LT", "LICI", "DLF", "BEL", "HAL", "BHEL", "ADANIPORTS", "CONCOR", "SIEMENS"
    ],

    "reliable_bluechips_v2": [
        "TCS", "HDFCBANK", "RELIANCE", "INFY", "HINDUNILVR", "ITC", 
        "LT", "ICICIBANK", "SBIN", "KOTAKBANK", "BAJFINANCE", "SRF",
        "PIDILITIND", "TITAN", "SUNPHARMA", "MARUTI", "ASIANPAINT",
        "ULTRACEMCO", "ADANIPORTS", "TRENT", "VBL"
    ],

    "defensive_v2": [
        "ONGC", "OIL", "HAL", "BEL", "MAZDOCK", "ADANIGREEN", 
        "TATAPOWER", "ITC", "NESTLEIND", "MUTHOOTFIN", "SOLARINDS"
    ],
}


def get_watchlist(name: str) -> list:
    """Return list of NSE ticker symbols for a given watchlist name."""
    name = name.lower().strip()
    if name not in WATCHLISTS:
        available = ", ".join(WATCHLISTS.keys())
        raise ValueError(
            f"Watchlist '{name}' not found. "
            f"Available: {available}"
        )
    return WATCHLISTS[name]


def list_watchlists() -> dict:
    """Return dict of watchlist name → count of stocks."""
    return {name: len(tickers) for name, tickers in WATCHLISTS.items()}


def add_to_custom(tickers: list):
    """Add tickers to the custom watchlist."""
    existing = WATCHLISTS["custom"]
    for t in tickers:
        t = t.upper().strip()
        if t not in existing:
            existing.append(t)
