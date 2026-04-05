#!/usr/bin/env python3
# =============================================================================
# main.py — NSE Stock Valuation Bot  |  Entry Point
#
# SINGLE STOCK:
#   python main.py INFY
#   python main.py HDFCBANK COALINDIA RELIANCE      ← multiple
#   python main.py INFY --export                     ← save Excel report
#   python main.py INFY --raw                        ← raw data only
#
# BATCH SCAN:
#   python main.py --scan nifty50
#   python main.py --scan value_quality --filter buy
#   python main.py --scan banking --filter buy --export
#   python main.py --scan custom --verbose
#
# WATCHLISTS AVAILABLE:
#   nifty50 | niftynext50 | midcap50 | value_quality
#   psu_dividend | banking | it_tech | pharma | cyclicals | custom
# =============================================================================

import sys
import argparse
from colorama import Fore, Style, init

init(autoreset=True)


# =============================================================================
# SINGLE STOCK PIPELINE
# =============================================================================

def run_single(symbol: str, raw_only: bool = False) -> dict:
    """Full valuation pipeline for one stock. Returns result dict."""

    from data.fetcher             import fetch_stock_data, print_raw_data
    from data.cleaner             import clean, validate
    from screening.detector       import detect
    from screening.quality_filter import run as quality_run
    from valuation.graham         import calculate as graham_calc
    from valuation.dcf            import calculate as dcf_calc
    from valuation.lynch          import calculate as lynch_calc
    from valuation.buffett        import calculate as buffett_calc
    from valuation.epv            import calculate as epv_calc
    from valuation.ddm            import calculate as ddm_calc
    from valuation.excess_returns import calculate as er_calc
    from valuation.ev_sales       import calculate as evs_calc
    from valuation.mid_cycle      import calculate as mc_calc
    from valuation.relative       import calculate as rel_calc
    from valuation.nav            import calculate as nav_calc
    from valuation.price_tam      import calculate as ptam_calc
    from verdict.aggregator       import aggregate
    from verdict.decision         import decide

    symbol = symbol.upper().strip()
    print(f"\n{Fore.CYAN}  [{symbol}] Starting valuation...{Style.RESET_ALL}")

    # ── Step 1: Fetch & Clean ──────────────────────────────────────────────
    raw = fetch_stock_data(symbol)
    if raw is None:
        print(f"{Fore.RED}  ✗ Could not fetch data for {symbol}{Style.RESET_ALL}")
        return None

    data = clean(raw)
    is_valid, warnings = validate(data)

    for w in warnings:
        color = Fore.RED if "CRITICAL" in w else Fore.YELLOW
        print(f"    {color}• {w}{Style.RESET_ALL}")

    if not is_valid:
        print(f"{Fore.RED}  ✗ Critical data missing — aborting.{Style.RESET_ALL}")
        return None

    if raw_only:
        print_raw_data(data)
        return {"symbol": symbol, "data": data}

    # ── Step 2: Detect Stock Type ──────────────────────────────────────────
    detection = detect(data)
    models    = detection.get("models_to_use", [])
    is_pharma = "pharma" in (data.get("sector") or "").lower()
    print(f"  ✓ Type: {Fore.MAGENTA}{detection['stock_type']}{Style.RESET_ALL}"
          f"  ({detection['reason']})")

    # ── Step 3: Quality Filter ─────────────────────────────────────────────
    quality    = quality_run(data)
    grade      = quality.get("grade", "N/A")
    score      = quality.get("score", 0)
    q_color    = (Fore.GREEN if "PASS" in grade else
                  Fore.YELLOW if "PARTIAL" in grade else Fore.RED)
    print(f"  ✓ Quality: {q_color}{grade} ({score}/100){Style.RESET_ALL}")

    # ── Step 4: Run Valuation Models ───────────────────────────────────────
    model_results = {}
    if "graham"         in models: model_results["Graham"]        = graham_calc(data)
    if "dcf"            in models: model_results["DCF"]           = dcf_calc(data, pharma_haircut=is_pharma)
    if "lynch"          in models: model_results["Lynch"]         = lynch_calc(data)
    if "buffett"        in models: model_results["Buffett"]       = buffett_calc(data)
    if "epv"            in models: model_results["EPV"]           = epv_calc(data)
    if "ddm"            in models: model_results["DDM"]           = ddm_calc(data)
    if "excess_returns" in models: model_results["ExcessReturns"] = er_calc(data)
    if "ev_sales"       in models: model_results["EV/Sales"]      = evs_calc(data)
    if "mid_cycle"      in models: model_results["MidCycleEV"]    = mc_calc(data)
    if "nav"            in models: model_results["NAV"]           = nav_calc(data)
    if "price_tam"      in models: model_results["PriceTAM"]      = ptam_calc(data)
    model_results["Relative"] = rel_calc(data)

    print(f"  ✓ Models run: {', '.join(m for m in model_results if model_results[m] and model_results[m].get('valid'))}")

    # ── Step 5: Aggregate ──────────────────────────────────────────────────
    agg  = aggregate(model_results, detection)
    w_iv = agg.get("weighted_iv")
    if w_iv:
        print(f"  ✓ Weighted IV: {Fore.CYAN}₹{w_iv:,.0f}{Style.RESET_ALL}"
              f"  (confidence: {agg.get('confidence')})")

    # ── Step 6: Decision ───────────────────────────────────────────────────
    cmp      = data.get("cmp")
    relative = model_results.get("Relative")
    decision = decide(cmp, agg, quality, relative, detection)
    verdict  = decision.get("verdict", "N/A")

    VERDICT_COLORS = {
        "STRONG BUY": Fore.GREEN + Style.BRIGHT,
        "BUY"       : Fore.GREEN,
        "HOLD"      : Fore.YELLOW,
        "OVERVALUED": Fore.RED,
        "AVOID"     : Fore.RED + Style.BRIGHT,
    }
    vc = VERDICT_COLORS.get(verdict, Fore.WHITE)
    print(f"  ✓ Verdict: {vc}{verdict}{Style.RESET_ALL}")

    # ── Step 7: Print Full Report ──────────────────────────────────────────
    from output.report import print_full_report
    print_full_report(data, detection, quality, model_results, agg, decision)

    return {
        "symbol"        : symbol,
        "name"          : data.get("name"),
        "cmp"           : cmp,
        "iv"            : w_iv,
        "discount"      : decision.get("discount_pct"),
        "verdict"       : verdict,
        "quality"       : grade,
        "type"          : detection.get("stock_type"),
        "data"          : data,
        "detection"     : detection,
        "quality_result": quality,
        "model_results" : model_results,
        "agg"           : agg,
        "decision"      : decision,
    }


# =============================================================================
# BATCH SUMMARY (multiple stocks, no scan)
# =============================================================================

def print_multi_summary(results: list):
    from tabulate import tabulate
    valid = [r for r in results if r]
    if not valid or len(valid) < 2:
        return

    VERDICT_COLORS = {
        "STRONG BUY": Fore.GREEN + Style.BRIGHT,
        "BUY"       : Fore.GREEN,
        "HOLD"      : Fore.YELLOW,
        "OVERVALUED": Fore.RED,
        "AVOID"     : Fore.RED + Style.BRIGHT,
    }

    sorted_r = sorted(valid, key=lambda x: x.get("discount") or -999, reverse=True)
    rows = []
    for r in sorted_r:
        cmp     = r.get("cmp")
        iv      = r.get("iv")
        disc    = r.get("discount")
        verdict = r.get("verdict", "N/A")
        vc      = VERDICT_COLORS.get(verdict, Fore.WHITE)
        rows.append([
            f"  {r.get('symbol',''):<14}",
            f"₹{cmp:,.0f}" if cmp else "N/A",
            f"₹{iv:,.0f}"  if iv  else "N/A",
            f"{disc:+.1f}%" if disc is not None else "N/A",
            r.get("quality", "N/A"),
            r.get("type", "N/A"),
            f"{vc}{verdict}{Style.RESET_ALL}",
        ])

    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"  COMPARISON SUMMARY — {len(valid)} stocks")
    print(f"{'='*70}{Style.RESET_ALL}")
    print(tabulate(rows,
                   headers=["  Ticker", "CMP", "IV", "Discount",
                             "Quality", "Type", "Verdict"],
                   tablefmt="plain"))
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    # ── Fetch Macro Data (live or simulated) ──────────────────────────────
    from data.fetcher import fetch_gsec_yield
    import config as cfg

    if cfg.SIMULATION_MODE:
        # V2 Simulation: skip live G-Sec fetch; use a period-appropriate value.
        # India 10Y G-Sec was ~6.75% in Dec 2024.  Kept as a constant here
        # so no external call is needed during historical backtesting.
        sim_gsec = 0.0675
        cfg.GSEC_10Y_YIELD = sim_gsec
        print(f"{Fore.MAGENTA}  [SIM] Simulation Mode ON"
              f" — {cfg.SIMULATED_YEAR}/{cfg.SIMULATED_MONTH}"
              f" | G-Sec: {sim_gsec*100:.2f}%{Style.RESET_ALL}")
    else:
        # V1 live behaviour — untouched
        live_yield = fetch_gsec_yield()
        if live_yield:
            cfg.GSEC_10Y_YIELD = live_yield
            print(f"{Fore.YELLOW}  ℹ Live India 10Y G-Sec: {live_yield*100:.2f}%{Style.RESET_ALL}")

    parser = argparse.ArgumentParser(
        description=(
            "NSE Stock Valuation Bot — India\n"
            "Supports: Graham, DCF, Lynch, Buffett Owner Earnings,\n"
            "          EPV, DDM, Excess Returns, EV/Sales, Mid-Cycle EV/EBITDA"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py INFY\n"
            "  python main.py INFY HDFCBANK COALINDIA\n"
            "  python main.py INFY --export\n"
            "  python main.py --scan nifty50\n"
            "  python main.py --scan value_quality --filter buy --export\n"
            "  python main.py --scan banking --filter undervalued\n"
            "\nWatchlists:\n"
            "  nifty50 | niftynext50 | midcap50 | value_quality\n"
            "  psu_dividend | banking | it_tech | pharma | cyclicals | custom"
        )
    )

    parser.add_argument(
        "tickers", nargs="*",
        help="NSE ticker(s) for single/multi stock analysis"
    )
    parser.add_argument(
        "--scan", metavar="WATCHLIST",
        help="Batch scan a preset watchlist"
    )
    parser.add_argument(
        "--filter", metavar="VERDICT",
        choices=["buy", "undervalued", "hold", "avoid"],
        help="Filter scan results: buy | undervalued | hold | avoid"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Export results to Excel (.xlsx)"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Show raw fetched financial data only"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print full report for each stock during batch scan"
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Seconds between API calls in scan mode (default: 1.5)"
    )
    parser.add_argument(
        "--lists", action="store_true",
        help="Show all available watchlists"
    )

    args = parser.parse_args()

    # ── Show watchlist menu ────────────────────────────────────────────────
    if args.lists:
        from screening.watchlists import list_watchlists
        print(f"\n{Fore.CYAN}  Available Watchlists:{Style.RESET_ALL}")
        for name, count in list_watchlists().items():
            print(f"    --scan {name:<20} ({count} stocks)")
        print()
        return

    # ── BATCH SCAN MODE ───────────────────────────────────────────────────
    if args.scan:
        from screening.watchlists import get_watchlist
        from screening.scanner    import run_scan, print_scan_summary

        try:
            tickers = get_watchlist(args.scan)
        except ValueError as e:
            print(f"{Fore.RED}  {e}{Style.RESET_ALL}")
            sys.exit(1)

        results = run_scan(
            tickers,
            filter_verdict=args.filter,
            delay=args.delay,
            verbose=args.verbose
        )
        print_scan_summary(results, watchlist_name=args.scan)

        if args.export and results:
            from output.export import export
            path = export(results)
            print(f"{Fore.GREEN}  ✓ Excel report saved: {path}{Style.RESET_ALL}\n")

        return

    # ── SINGLE / MULTI STOCK MODE ─────────────────────────────────────────
    if not args.tickers:
        parser.print_help()
        return

    results = []
    for ticker in args.tickers:
        result = run_single(ticker, raw_only=args.raw)
        results.append(result)

    # Multi-stock comparison table
    if len(results) > 1 and not args.raw:
        print_multi_summary(results)

    # Export
    if args.export and not args.raw:
        valid = [r for r in results if r]
        if valid:
            from output.export import export
            path = export(valid)
            print(f"{Fore.GREEN}  ✓ Excel report saved: {path}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
