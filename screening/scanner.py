# =============================================================================
# screening/scanner.py — Batch Stock Scanner
#
# Scans a list of NSE stocks, runs full valuation on each,
# filters by verdict, and exports results to Excel.
#
# Usage (from main.py):
#   python main.py --scan nifty50
#   python main.py --scan value_quality --filter buy
#   python main.py --scan banking --export
# =============================================================================

import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_scan(tickers: list,
             filter_verdict: str = None,
             delay: float = 1.5,
             verbose: bool = False) -> list:
    """
    Scan a list of tickers. Returns list of full result dicts.

    filter_verdict : "buy" → show only STRONG BUY + BUY
                     "undervalued" → show only stocks with discount > 0
                     None → show all
    delay          : seconds between API calls (avoid rate limits)
    verbose        : if True, print full report for each stock
    """
    from colorama import Fore, Style, init
    from tqdm import tqdm
    init(autoreset=True)

    # Import the full pipeline from main.py
    from data.fetcher  import fetch_stock_data, print_raw_data
    from data.cleaner  import clean, validate
    from screening.detector      import detect
    from screening.quality_filter import run as quality_run
    from valuation.graham        import calculate as graham_calc
    from valuation.dcf           import calculate as dcf_calc
    from valuation.lynch         import calculate as lynch_calc
    from valuation.buffett       import calculate as buffett_calc
    from valuation.epv           import calculate as epv_calc
    from valuation.ddm           import calculate as ddm_calc
    from valuation.excess_returns import calculate as er_calc
    from valuation.ev_sales      import calculate as evs_calc
    from valuation.mid_cycle     import calculate as mc_calc
    from valuation.relative      import calculate as rel_calc
    from verdict.aggregator      import aggregate
    from verdict.decision        import decide

    results = []
    failed  = []

    print(f"\n{Fore.CYAN}{'='*62}")
    print(f"  BATCH SCANNER — {len(tickers)} stocks")
    if filter_verdict:
        print(f"  Filter: {filter_verdict.upper()}")
    print(f"{'='*62}{Style.RESET_ALL}\n")

    for ticker in tqdm(tickers, desc="  Scanning", unit="stock",
                       bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}"):
        try:
            symbol = ticker.upper().strip()

            # ── Fetch + Clean ──────────────────────────────────────────────
            raw = fetch_stock_data(symbol)
            if raw is None:
                failed.append((symbol, "Fetch failed"))
                time.sleep(delay)
                continue

            data = clean(raw)
            is_valid, _ = validate(data)
            if not is_valid:
                failed.append((symbol, "Validation failed"))
                time.sleep(delay)
                continue

            # ── Detect ────────────────────────────────────────────────────
            detection = detect(data)
            models    = detection.get("models_to_use", [])
            is_pharma = "pharma" in (data.get("sector") or "").lower()

            # ── Quality ───────────────────────────────────────────────────
            quality = quality_run(data)

            # ── Valuation Models ──────────────────────────────────────────
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
            model_results["Relative"] = rel_calc(data)

            # ── Aggregate + Decide ────────────────────────────────────────
            agg      = aggregate(model_results, detection)
            relative = model_results.get("Relative")
            decision = decide(data.get("cmp"), agg, quality, relative, detection)

            verdict  = decision.get("verdict", "N/A")
            discount = decision.get("discount_pct")
            iv       = agg.get("weighted_iv")
            cmp      = data.get("cmp")

            result = {
                "symbol"        : symbol,
                "name"          : data.get("name"),
                "cmp"           : cmp,
                "iv"            : iv,
                "discount"      : discount,
                "verdict"       : verdict,
                "quality"       : quality.get("grade"),
                "type"          : detection.get("stock_type"),
                "data"          : data,
                "detection"     : detection,
                "quality_result": quality,
                "model_results" : model_results,
                "agg"           : agg,
                "decision"      : decision,
            }

            if verbose:
                from output.report import print_full_report
                print_full_report(data, detection, quality,
                                  model_results, agg, decision)

            results.append(result)

        except Exception as e:
            failed.append((ticker, str(e)))

        time.sleep(delay)

    # ── Filter ────────────────────────────────────────────────────────────
    if filter_verdict:
        fv = filter_verdict.lower()
        if fv == "buy":
            results = [r for r in results
                       if r.get("verdict") in ["STRONG BUY", "BUY"]]
        elif fv == "undervalued":
            results = [r for r in results
                       if (r.get("discount") or 0) > 0]
        elif fv == "hold":
            results = [r for r in results if r.get("verdict") == "HOLD"]
        elif fv == "avoid":
            results = [r for r in results
                       if r.get("verdict") in ["OVERVALUED", "AVOID"]]

    # ── Print Failures ────────────────────────────────────────────────────
    if failed:
        print(f"\n{Fore.YELLOW}  Skipped {len(failed)} stocks:{Style.RESET_ALL}")
        for sym, reason in failed:
            print(f"  • {sym}: {reason}")

    return results


def print_scan_summary(results: list, watchlist_name: str = ""):
    """Print a ranked summary table of scan results."""
    from tabulate import tabulate
    from colorama import Fore, Style, init
    init(autoreset=True)

    if not results:
        print(f"\n{Fore.YELLOW}  No stocks match the filter criteria.{Style.RESET_ALL}")
        return

    VERDICT_COLORS = {
        "STRONG BUY"              : Fore.GREEN + Style.BRIGHT,
        "BUY"                     : Fore.GREEN,
        "HOLD"                    : Fore.YELLOW,
        "OVERVALUED"              : Fore.RED,
        "AVOID"                   : Fore.RED + Style.BRIGHT,
        "EARLY STAGE — SPECULATIVE": Fore.YELLOW,
    }

    sorted_r = sorted(results, key=lambda x: x.get("discount") or -999, reverse=True)

    # Counts
    strong_buy = sum(1 for r in results if r.get("verdict") == "STRONG BUY")
    buy        = sum(1 for r in results if r.get("verdict") == "BUY")
    hold       = sum(1 for r in results if r.get("verdict") == "HOLD")
    overv      = sum(1 for r in results if r.get("verdict") in ["OVERVALUED", "AVOID"])

    print(f"\n{Fore.CYAN}{'='*75}")
    title = f"  SCAN RESULTS — {watchlist_name.upper()}" if watchlist_name else "  SCAN RESULTS"
    print(f"{title}  ({len(results)} stocks)")
    print(f"{'='*75}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN + Style.BRIGHT}STRONG BUY: {strong_buy}{Style.RESET_ALL}  "
          f"  {Fore.GREEN}BUY: {buy}{Style.RESET_ALL}  "
          f"  {Fore.YELLOW}HOLD: {hold}{Style.RESET_ALL}  "
          f"  {Fore.RED}OVERVALUED/AVOID: {overv}{Style.RESET_ALL}")
    print()

    rows = []
    for r in sorted_r:
        cmp     = r.get("cmp")
        iv      = r.get("iv")
        disc    = r.get("discount")
        verdict = r.get("verdict", "N/A")
        vc      = VERDICT_COLORS.get(verdict, Fore.WHITE)
        quality = r.get("quality", "N/A")

        rows.append([
            f"  {r.get('symbol', ''):<14}",
            (r.get("name") or "")[:28],
            f"₹{cmp:,.0f}" if cmp else "N/A",
            f"₹{iv:,.0f}"  if iv  else "N/A",
            f"{disc:+.1f}%" if disc is not None else "N/A",
            r.get("type", "N/A"),
            quality,
            f"{vc}{verdict}{Style.RESET_ALL}",
        ])

    print(tabulate(
        rows,
        headers=["  Ticker", "Name", "CMP", "IV", "Discount", "Type", "Quality", "Verdict"],
        tablefmt="plain"
    ))

    # Top picks
    top = [r for r in sorted_r if r.get("verdict") in ["STRONG BUY", "BUY"]]
    if top:
        print(f"\n{Fore.GREEN + Style.BRIGHT}  TOP PICKS (BUY / STRONG BUY):{Style.RESET_ALL}")
        for r in top[:10]:
            disc = r.get("discount")
            print(f"  ★ {r.get('symbol'):<14} "
                  f"₹{r.get('cmp') or 0:,.0f}  →  IV ₹{r.get('iv') or 0:,.0f}  "
                  f"({disc:+.1f}% discount)  {r.get('quality')}")

    print()
