# =============================================================================
# output/report.py — Coloured Terminal Report Generator
# =============================================================================

from colorama import Fore, Back, Style, init
from tabulate import tabulate
import sys, os

init(autoreset=True)

# Verdict colours
VERDICT_COLORS = {
    "STRONG BUY"              : Fore.GREEN + Style.BRIGHT,
    "BUY"                     : Fore.GREEN,
    "HOLD"                    : Fore.YELLOW,
    "OVERVALUED"              : Fore.RED,
    "AVOID"                   : Fore.RED + Style.BRIGHT,
    "EARLY STAGE — SPECULATIVE": Fore.YELLOW + Style.BRIGHT,
}

SEP  = "=" * 62
SEP2 = "-" * 62


def print_full_report(data: dict, detection: dict, quality: dict,
                      model_results: dict, agg: dict, decision: dict):
    """Print the complete formatted valuation report to terminal."""

    name   = data.get("name", data.get("symbol", "Unknown"))
    symbol = data.get("symbol", "")
    sector = data.get("sector", "N/A")
    cmp    = data.get("cmp")
    mktcap = data.get("market_cap")

    verdict       = decision.get("verdict", "N/A")
    verdict_color = VERDICT_COLORS.get(verdict, Fore.WHITE)

    # ── Header ─────────────────────────────────────────────────────────────
    import config as cfg
    date_str = ""
    if cfg.SIMULATED_YEAR and cfg.SIMULATED_MONTH:
        # Map number month to name if possible, or just use as is
        from calendar import month_name
        try:
            m_name = month_name[int(cfg.SIMULATED_MONTH)]
            date_str = f" | Period: {m_name} {cfg.SIMULATED_YEAR}"
        except (ValueError, IndexError):
            date_str = f" | Period: {cfg.SIMULATED_MONTH}/{cfg.SIMULATED_YEAR}"

    print(f"\n{Fore.CYAN}{SEP}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  STOCK VALUATION REPORT{date_str}{Style.RESET_ALL}")
    print(f"  {name}  ({symbol})")
    print(f"  Sector: {sector}  |  Stock Type: {detection.get('stock_type', 'N/A')}")
    if cmp:
        print(f"  CMP: ₹{cmp:,.2f}", end="")
    if mktcap:
        print(f"  |  Market Cap: ₹{mktcap/1e7:,.0f} Cr")
    else:
        print()
    print(f"{Fore.CYAN}{SEP}{Style.RESET_ALL}")

    # ── Stock type warning (e.g. cyclical, early-stage) ───────────────────
    if detection.get("warning"):
        print(f"\n{Fore.YELLOW}{detection['warning']}{Style.RESET_ALL}")

    # ── Quality Gate ──────────────────────────────────────────────────────
    grade = quality.get("grade", "N/A")
    score = quality.get("score", 0)
    g_color = (Fore.GREEN if "PASS" in grade else
               Fore.YELLOW if "PARTIAL" in grade else Fore.RED)

    print(f"\n{Fore.WHITE + Style.BRIGHT}  QUALITY GATE{Style.RESET_ALL}")
    print(SEP2)
    print(f"  Score: {g_color}{score}/100  —  {grade}{Style.RESET_ALL}")
    print(f"  Passed : {Fore.GREEN}{', '.join(quality.get('passed', [])) or 'None'}{Style.RESET_ALL}")
    if quality.get("failed"):
        print(f"  Failed : {Fore.RED}{', '.join(quality['failed'])}{Style.RESET_ALL}")
    if quality.get("moat_flags"):
        print(f"  Moat   : {Fore.CYAN}{' | '.join(quality['moat_flags'])}{Style.RESET_ALL}")

    # ── Intrinsic Value Models ────────────────────────────────────────────
    print(f"\n{Fore.WHITE + Style.BRIGHT}  INTRINSIC VALUE ESTIMATES{Style.RESET_ALL}")
    print(SEP2)

    rows = []
    for model_name, result in model_results.items():
        if result is None:
            continue
        iv   = result.get("iv")
        note = result.get("note", "")[:50] if result.get("note") else ""
        valid= result.get("valid", False)

        if not valid:
            iv_str = f"{Fore.RED}SKIPPED{Style.RESET_ALL}"
            note   = result.get("note", "")[:55]
        elif iv is None:
            iv_str = "N/A"
        else:
            # Colour IV vs CMP
            if cmp and iv > cmp * 1.30:
                iv_str = f"{Fore.GREEN}₹{iv:,.0f}{Style.RESET_ALL}"
            elif cmp and iv < cmp * 0.90:
                iv_str = f"{Fore.RED}₹{iv:,.0f}{Style.RESET_ALL}"
            else:
                iv_str = f"₹{iv:,.0f}"

        rows.append([f"  {model_name}", iv_str, note])

    if rows:
        print(tabulate(rows, headers=["  Model", "Intrinsic Value", "Note"],
                       tablefmt="plain"))

    # ── Weighted IV Summary ───────────────────────────────────────────────
    w_iv  = agg.get("weighted_iv")
    iv_lo, iv_hi = agg.get("iv_range", (None, None))

    print(f"\n{Fore.WHITE + Style.BRIGHT}  WEIGHTED INTRINSIC VALUE{Style.RESET_ALL}")
    print(SEP2)
    if w_iv:
        print(f"  Weighted IV  : {Fore.CYAN + Style.BRIGHT}₹{w_iv:,.0f}{Style.RESET_ALL}"
              f"  (range ₹{iv_lo:,.0f} – ₹{iv_hi:,.0f})")
        print(f"  Confidence   : {agg.get('confidence', 'N/A')}")
        weights_str = ", ".join(
            f"{m} {w*100:.0f}%"
            for m, w in agg.get("weights_used", {}).items()
        )
        print(f"  Weights      : {weights_str}")
    else:
        print(f"  {Fore.RED}Could not compute weighted IV{Style.RESET_ALL}")

    # ── Margin of Safety ─────────────────────────────────────────────────
    discount_pct = decision.get("discount_pct")
    if cmp and w_iv and discount_pct is not None:
        print(f"\n{Fore.WHITE + Style.BRIGHT}  MARGIN OF SAFETY{Style.RESET_ALL}")
        print(SEP2)
        mos_color = (Fore.GREEN if discount_pct >= 15 else
                     Fore.YELLOW if discount_pct >= 0 else Fore.RED)
        print(f"  CMP          : ₹{cmp:,.2f}")
        print(f"  Weighted IV  : ₹{w_iv:,.0f}")
        print(f"  Discount     : {mos_color}{discount_pct:+.1f}%  "
              f"({decision.get('margin_verdict', '')}){Style.RESET_ALL}")

    # ── Relative Valuation ────────────────────────────────────────────────
    rel = model_results.get("Relative")
    if rel and rel.get("valid"):
        print(f"\n{Fore.WHITE + Style.BRIGHT}  RELATIVE VALUATION vs PEERS{Style.RESET_ALL}")
        print(SEP2)
        metrics     = rel.get("metrics", {})
        benchmarks  = rel.get("sector_medians", {})
        comparisons = rel.get("comparisons", {})

        rel_rows = []
        metric_labels = {"pe": "P/E", "pb": "P/B",
                         "ev_ebitda": "EV/EBITDA", "peg": "PEG"}
        for key, label in metric_labels.items():
            stock_val = metrics.get(key)
            bench_val = benchmarks.get(key)
            comp      = comparisons.get(key, {})
            status    = comp.get("status", "N/A")
            s_color   = (Fore.GREEN if status == "CHEAP" else
                         Fore.RED if status == "EXPENSIVE" else Fore.WHITE)
            sv_str = f"{stock_val:.1f}x" if stock_val else "N/A"
            bv_str = f"{bench_val:.1f}x" if bench_val else "N/A"
            rel_rows.append([
                f"  {label}", sv_str, bv_str,
                f"{s_color}{status}{Style.RESET_ALL}"
            ])
        print(tabulate(rel_rows,
                       headers=["  Metric", "Stock", "Sector Median", "Status"],
                       tablefmt="plain"))

        overall = rel.get("overall_relative", "N/A")
        ov_color= (Fore.GREEN if "CHEAP" in overall else
                   Fore.RED if "EXPENSIVE" in overall else Fore.WHITE)
        print(f"\n  Overall      : {ov_color}{overall}{Style.RESET_ALL}")

    # ── Buffett Earnings Yield ────────────────────────────────────────────
    buff = model_results.get("Buffett")
    if buff and buff.get("valid") and buff.get("earnings_yield"):
        ey = buff["earnings_yield"]
        gsec = buff["gsec_yield"]
        ey_color = Fore.GREEN if ey >= gsec else Fore.RED
        print(f"\n  Earnings Yield: {ey_color}{ey:.2f}%{Style.RESET_ALL}"
              f"  vs G-Sec {gsec:.1f}%  →  {buff.get('yield_verdict', '')}")

    # ── Flags ─────────────────────────────────────────────────────────────
    flags = decision.get("flags", [])
    if flags:
        print(f"\n{Fore.WHITE + Style.BRIGHT}  FLAGS & NOTES{Style.RESET_ALL}")
        print(SEP2)
        for flag in flags:
            print(f"  {flag}")

    # ── Final Verdict ─────────────────────────────────────────────────────
    print(f"\n{Fore.WHITE + Style.BRIGHT}{SEP}{Style.RESET_ALL}")
    print(f"  FINAL VERDICT:  {verdict_color}{verdict}{Style.RESET_ALL}")
    print(f"  Action: {decision.get('action', '')}")
    print(f"  {decision.get('rationale', '')}")
    print(f"{Fore.WHITE + Style.BRIGHT}{SEP}{Style.RESET_ALL}\n")
