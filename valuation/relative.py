# =============================================================================
# valuation/relative.py — Relative Valuation (Peer Comparison)
#
# Computes: P/E, EV/EBITDA, P/B, PEG
# Compares vs: sector medians (hardcoded benchmarks + live where possible)
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# India sector median multiples (Nifty 500 universe, approximate)
# Update these periodically as market conditions change
SECTOR_MEDIANS = {
    "Information Technology": {"pe": 25, "ev_ebitda": 18, "pb": 6.0},
    "Technology"            : {"pe": 25, "ev_ebitda": 18, "pb": 6.0},
    "Financial Services"    : {"pe": 18, "ev_ebitda": None, "pb": 2.5},
    "Banking"               : {"pe": 16, "ev_ebitda": None, "pb": 2.0},
    "Healthcare"            : {"pe": 28, "ev_ebitda": 18, "pb": 4.0},
    "Pharmaceutical"        : {"pe": 28, "ev_ebitda": 18, "pb": 4.0},
    "Consumer Defensive"    : {"pe": 45, "ev_ebitda": 30, "pb": 8.0},
    "Consumer Cyclical"     : {"pe": 35, "ev_ebitda": 20, "pb": 5.0},
    "Basic Materials"       : {"pe": 12, "ev_ebitda": 7,  "pb": 1.5},
    "Energy"                : {"pe": 14, "ev_ebitda": 8,  "pb": 1.8},
    "Industrials"           : {"pe": 30, "ev_ebitda": 18, "pb": 4.0},
    "Utilities"             : {"pe": 18, "ev_ebitda": 10, "pb": 2.0},
    "Real Estate"           : {"pe": 30, "ev_ebitda": 20, "pb": 3.0},
    "Communication Services": {"pe": 22, "ev_ebitda": 12, "pb": 3.0},
    "default"               : {"pe": 22, "ev_ebitda": 14, "pb": 3.0},
}


def calculate(data: dict) -> dict:
    """
    Returns:
      {
        "model"            : "Relative",
        "iv"               : None,   # Relative doesn't give a single IV
        "metrics"          : dict,   # Stock's own multiples
        "sector_medians"   : dict,   # Benchmark for comparison
        "comparisons"      : dict,   # CHEAP / FAIR / EXPENSIVE per metric
        "overall_relative" : str,    # Overall cheap/fair/expensive vs peers
        "note"             : str,
        "valid"            : bool
      }
    """
    pe       = data.get("pe_ratio")
    pb       = data.get("pb_ratio")
    ev_ebitda= data.get("ev_ebitda")
    sector   = data.get("sector") or "default"
    eps      = data.get("eps_ttm")
    cmp      = data.get("cmp")
    g_rate   = data.get("eps_growth_5y") or 0

    # Compute PEG
    if pe and g_rate and g_rate > 0:
        peg = pe / (g_rate * 100)
    else:
        peg = None

    # Compute P/E if missing
    if not pe and eps and eps > 0 and cmp:
        pe = cmp / eps

    # ── Sector Benchmarks ─────────────────────────────────────────────────
    benchmarks = _get_benchmarks(sector)

    # ── Metric-by-metric comparison ───────────────────────────────────────
    comparisons = {}

    if pe and benchmarks.get("pe"):
        comparisons["pe"] = _compare(pe, benchmarks["pe"],
                                     low_is_cheap=True, label="P/E")

    if pb and benchmarks.get("pb"):
        comparisons["pb"] = _compare(pb, benchmarks["pb"],
                                     low_is_cheap=True, label="P/B")

    if ev_ebitda and benchmarks.get("ev_ebitda"):
        comparisons["ev_ebitda"] = _compare(ev_ebitda, benchmarks["ev_ebitda"],
                                            low_is_cheap=True, label="EV/EBITDA")

    if peg:
        if peg < 1.0:
            comparisons["peg"] = {"status": "CHEAP", "detail": f"PEG {peg:.2f} < 1 → Undervalued vs growth"}
        elif peg <= 2.0:
            comparisons["peg"] = {"status": "FAIR",  "detail": f"PEG {peg:.2f} in 1–2 → Fairly valued"}
        else:
            comparisons["peg"] = {"status": "EXPENSIVE", "detail": f"PEG {peg:.2f} > 2 → Expensive vs growth"}

    # ── Overall relative verdict ──────────────────────────────────────────
    statuses  = [c["status"] for c in comparisons.values()]
    cheap_ct  = statuses.count("CHEAP")
    exp_ct    = statuses.count("EXPENSIVE")
    total     = len(statuses)

    if total == 0:
        overall = "INSUFFICIENT DATA"
    elif cheap_ct / total >= 0.6:
        overall = "CHEAP vs PEERS"
    elif exp_ct / total >= 0.6:
        overall = "EXPENSIVE vs PEERS"
    else:
        overall = "IN LINE WITH PEERS"

    note = f"Compared vs {sector} sector medians (Nifty 500 universe)"

    return {
        "model"           : "Relative",
        "iv"              : None,   # Relative valuation doesn't give intrinsic value
        "metrics"         : {
            "pe"       : round(pe, 1) if pe else None,
            "pb"       : round(pb, 1) if pb else None,
            "ev_ebitda": round(ev_ebitda, 1) if ev_ebitda else None,
            "peg"      : round(peg, 2) if peg else None,
        },
        "sector_medians"  : benchmarks,
        "comparisons"     : comparisons,
        "overall_relative": overall,
        "note"            : note,
        "valid"           : len(comparisons) > 0
    }


def _get_benchmarks(sector: str) -> dict:
    for key in SECTOR_MEDIANS:
        if key.lower() in sector.lower():
            return SECTOR_MEDIANS[key]
    return SECTOR_MEDIANS["default"]


def _compare(value: float, benchmark: float,
             low_is_cheap: bool = True, label: str = "") -> dict:
    """Returns status (CHEAP/FAIR/EXPENSIVE) based on % deviation from benchmark."""
    pct_diff = (value - benchmark) / benchmark * 100

    if low_is_cheap:
        if pct_diff <= -20:
            status = "CHEAP"
        elif pct_diff >= 20:
            status = "EXPENSIVE"
        else:
            status = "FAIR"
        detail = f"{label} {value:.1f}x vs sector {benchmark}x ({pct_diff:+.1f}%)"
    else:
        if pct_diff >= 20:
            status = "CHEAP"
        elif pct_diff <= -20:
            status = "EXPENSIVE"
        else:
            status = "FAIR"
        detail = f"{label} {value:.1f}x vs sector {benchmark}x ({pct_diff:+.1f}%)"

    return {"status": status, "detail": detail}
