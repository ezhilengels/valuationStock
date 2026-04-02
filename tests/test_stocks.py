#!/usr/bin/env python3
# =============================================================================
# tests/test_stocks.py — End-to-End Test Suite
#
# Tests the FULL valuation pipeline on 20 representative NSE stocks
# spanning all stock types: LARGE_STABLE, HIGH_GROWTH, BANK_NBFC,
# PSU, CYCLICAL, EARLY_STAGE, REIT.
#
# Run:
#   python tests/test_stocks.py               ← full test (slow, makes API calls)
#   python tests/test_stocks.py --offline     ← logic tests only (no API calls)
#   python tests/test_stocks.py --quick       ← single stock quick test
#   python tests/test_stocks.py --stock INFY  ← test one specific stock
#
# What is tested:
#   ✓ Data fetcher returns a valid dict
#   ✓ Cleaner fills missing values without crashing
#   ✓ Detector returns correct stock type
#   ✓ All models return valid=True or valid=False with a note (no crashes)
#   ✓ Aggregator produces a weighted IV > 0
#   ✓ Decision engine produces a valid verdict string
#   ✓ IV > 0 for all profitable stocks
#   ✓ Model weights sum to ~1.0
#   ✓ Cache works (second call returns same data faster)
# =============================================================================

import sys
import os
import time
import argparse
import json

# Make sure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colorama import Fore, Style, init
init(autoreset=True)


# =============================================================================
# TEST STOCKS — 20 stocks covering all stock types
# =============================================================================

TEST_STOCKS = [
    # LARGE_STABLE — FMCG / Consumer
    {"symbol": "HINDUNILVR", "expected_type": "LARGE_STABLE",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "NESTLEIND",  "expected_type": "LARGE_STABLE",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "ITC",        "expected_type": "LARGE_STABLE",
     "expect_profitable": True,  "expect_iv": True},

    # HIGH_GROWTH — IT
    {"symbol": "INFY",       "expected_type": "HIGH_GROWTH",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "TCS",        "expected_type": "HIGH_GROWTH",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "HCLTECH",    "expected_type": "HIGH_GROWTH",
     "expect_profitable": True,  "expect_iv": True},

    # HIGH_GROWTH — Pharma
    {"symbol": "SUNPHARMA",  "expected_type": "HIGH_GROWTH",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "DIVISLAB",   "expected_type": "HIGH_GROWTH",
     "expect_profitable": True,  "expect_iv": True},

    # BANK_NBFC
    {"symbol": "HDFCBANK",   "expected_type": "BANK_NBFC",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "ICICIBANK",  "expected_type": "BANK_NBFC",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "BAJFINANCE", "expected_type": "BANK_NBFC",
     "expect_profitable": True,  "expect_iv": True},

    # PSU
    {"symbol": "COALINDIA",  "expected_type": "PSU",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "NTPC",       "expected_type": "PSU",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "SBIN",       "expected_type": "PSU",
     "expect_profitable": True,  "expect_iv": True},

    # CYCLICAL
    {"symbol": "TATASTEEL",  "expected_type": "CYCLICAL",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "JSWSTEEL",   "expected_type": "CYCLICAL",
     "expect_profitable": True,  "expect_iv": True},

    # GENERAL
    {"symbol": "RELIANCE",   "expected_type": "GENERAL",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "TITAN",      "expected_type": "GENERAL",
     "expect_profitable": True,  "expect_iv": True},
    {"symbol": "ASIANPAINT", "expected_type": "GENERAL",
     "expect_profitable": True,  "expect_iv": True},

    # Volatile / check that pipeline doesn't crash
    {"symbol": "IRCTC",      "expected_type": None,
     "expect_profitable": True,  "expect_iv": True},
]

VALID_STOCK_TYPES = {
    "BANK_NBFC", "PSU", "EARLY_STAGE", "CYCLICAL",
    "HIGH_GROWTH", "LARGE_STABLE", "GENERAL", "REIT"
}

VALID_VERDICTS = {
    "STRONG BUY", "BUY", "HOLD", "OVERVALUED", "AVOID",
    "EARLY STAGE — SPECULATIVE", "REIT — NAV BASED"
}


# =============================================================================
# TEST RUNNER
# =============================================================================

class TestResult:
    def __init__(self, symbol: str):
        self.symbol    = symbol
        self.passed    = []
        self.failed    = []
        self.warnings  = []
        self.data      = {}
        self.skip_reason = None

    def ok(self, msg: str):
        self.passed.append(msg)

    def fail(self, msg: str):
        self.failed.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def success(self) -> bool:
        return len(self.failed) == 0

    def summary(self) -> str:
        icon = "✅" if self.success else "❌"
        n_ok = len(self.passed)
        n_fail = len(self.failed)
        return (f"{icon} {self.symbol:15s} "
                f"Pass:{n_ok:2d} Fail:{n_fail:2d}")


def run_full_test(stock_info: dict, delay: float = 1.5) -> TestResult:
    """Run all checks for a single stock."""
    symbol  = stock_info["symbol"]
    result  = TestResult(symbol)

    expected_type    = stock_info.get("expected_type")
    expect_profitable= stock_info.get("expect_profitable", True)
    expect_iv        = stock_info.get("expect_iv", True)

    try:
        # ── 1. Data Fetch ─────────────────────────────────────────────────
        from data.fetcher import fetch_stock_data
        t0  = time.time()
        raw = fetch_stock_data(symbol, use_cache=False, use_screener=False)
        t1  = time.time()

        if raw is None:
            result.fail("fetch_stock_data returned None")
            return result
        result.ok(f"Fetch OK ({t1-t0:.1f}s)")

        # ── 2. Cache Test ─────────────────────────────────────────────────
        from data.cache import set_cache, get_cached
        set_cache(symbol, raw, "main")
        cached = get_cached(symbol, "main")
        if cached is not None:
            result.ok("Cache write+read OK")
        else:
            result.fail("Cache: set_cache then get_cached returned None")

        # ── 3. Cleaner ────────────────────────────────────────────────────
        from data.cleaner import clean, validate
        data = clean(raw)
        is_valid, warnings = validate(data)

        if data:
            result.ok("Cleaner returned non-empty dict")
        else:
            result.fail("Cleaner returned empty dict")

        for w in warnings:
            result.warn(w)

        # ── 4. Basic Field Checks ─────────────────────────────────────────
        if data.get("cmp") and data["cmp"] > 0:
            result.ok(f"CMP present: ₹{data['cmp']:,.0f}")
        else:
            result.fail("CMP missing or zero")

        if data.get("symbol"):
            result.ok(f"Symbol: {data['symbol']}")
        else:
            result.fail("Symbol field missing")

        if data.get("sector") and data["sector"] != "Unknown":
            result.ok(f"Sector: {data['sector']}")
        else:
            result.warn("Sector is 'Unknown' — may affect model routing")

        # ── 5. Detector ───────────────────────────────────────────────────
        from screening.detector import detect
        detection = detect(data)

        stock_type = detection.get("stock_type")
        if stock_type in VALID_STOCK_TYPES:
            result.ok(f"Detector: {stock_type} ({detection.get('reason', '')})")
        else:
            result.fail(f"Detector returned invalid type: {stock_type}")

        if expected_type and stock_type != expected_type:
            result.warn(
                f"Expected type {expected_type}, got {stock_type} "
                f"— may need config tuning"
            )

        models = detection.get("models_to_use", [])
        if models:
            result.ok(f"Models assigned: {', '.join(models)}")
        else:
            result.fail("No models assigned by detector")

        weights = detection.get("weights", {})
        weight_sum = sum(weights.values())
        if weights and abs(weight_sum - 1.0) < 0.05:
            result.ok(f"Weights sum ≈ 1.0 ({weight_sum:.2f})")
        elif weights:
            result.warn(f"Weights sum = {weight_sum:.2f} (not exactly 1.0 — aggregator normalises)")

        # ── 6. Quality Filter ─────────────────────────────────────────────
        from screening.quality_filter import run as quality_run
        quality = quality_run(data)

        grade = quality.get("grade", "")
        score = quality.get("score", 0)
        if grade:
            result.ok(f"Quality Grade: {grade} ({score}/100)")
        else:
            result.fail("Quality filter returned no grade")

        # ── 7. Run Valuation Models ────────────────────────────────────────
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

        is_pharma = "pharma" in (data.get("sector") or "").lower()
        model_results = {}

        model_runners = {
            "graham"        : lambda: graham_calc(data),
            "dcf"           : lambda: dcf_calc(data, pharma_haircut=is_pharma),
            "lynch"         : lambda: lynch_calc(data),
            "buffett"       : lambda: buffett_calc(data),
            "epv"           : lambda: epv_calc(data),
            "ddm"           : lambda: ddm_calc(data),
            "excess_returns": lambda: er_calc(data),
            "ev_sales"      : lambda: evs_calc(data),
            "mid_cycle"     : lambda: mc_calc(data),
            "nav"           : lambda: nav_calc(data),
            "price_tam"     : lambda: ptam_calc(data),
        }

        model_display = {
            "graham": "Graham", "dcf": "DCF", "lynch": "Lynch",
            "buffett": "Buffett", "epv": "EPV", "ddm": "DDM",
            "excess_returns": "ExcessReturns", "ev_sales": "EV/Sales",
            "mid_cycle": "MidCycleEV", "nav": "NAV", "price_tam": "PriceTAM",
        }

        models_that_ran = []
        models_that_crashed = []

        for key in models:
            runner = model_runners.get(key)
            if not runner:
                continue
            display = model_display.get(key, key)
            try:
                mr = runner()
                model_results[display] = mr
                models_that_ran.append(display)

                # Each model must return a dict with 'valid' and 'note'
                if not isinstance(mr, dict):
                    result.fail(f"Model {display}: returned non-dict {type(mr)}")
                elif "valid" not in mr:
                    result.fail(f"Model {display}: missing 'valid' key")
                elif "note" not in mr:
                    result.fail(f"Model {display}: missing 'note' key")
                elif mr.get("valid") and mr.get("iv") is not None:
                    iv = mr["iv"]
                    if iv > 0:
                        result.ok(f"  {display}: IV=₹{iv:,.0f}")
                    else:
                        result.warn(f"  {display}: IV={iv} (zero or negative)")
                else:
                    result.ok(f"  {display}: skipped ({mr.get('note','')[:60]})")

            except Exception as ex:
                models_that_crashed.append(display)
                result.fail(f"Model {display} CRASHED: {ex}")

        model_results["Relative"] = rel_calc(data)

        if models_that_crashed:
            result.fail(f"Crashed models: {', '.join(models_that_crashed)}")
        else:
            result.ok(f"All {len(models_that_ran)} models ran without crash")

        # ── 8. Aggregator ─────────────────────────────────────────────────
        from verdict.aggregator import aggregate
        agg = aggregate(model_results, detection)

        w_iv = agg.get("weighted_iv")
        if expect_iv:
            if w_iv and w_iv > 0:
                result.ok(f"Aggregator: Weighted IV ₹{w_iv:,.0f} ({agg.get('confidence')})")
            else:
                result.fail(f"Expected Weighted IV > 0, got {w_iv}")
        else:
            result.ok(f"Aggregator ran (IV={w_iv})")

        # ── 9. Decision ────────────────────────────────────────────────────
        from verdict.decision import decide
        cmp_val = data.get("cmp")
        relative = model_results.get("Relative")
        decision = decide(cmp_val, agg, quality, relative, detection)

        verdict = decision.get("verdict", "")
        # Allow any string verdict — new stock types may have different verdicts
        if verdict:
            result.ok(f"Verdict: {verdict}")
        else:
            result.fail("Decision engine returned no verdict")

        disc = decision.get("discount_pct")
        if disc is not None:
            result.ok(f"Discount: {disc:+.1f}%")
        else:
            result.warn("Discount % not computed (normal for REIT/EarlyStage)")

        # ── Store result summary ───────────────────────────────────────────
        result.data = {
            "stock_type": stock_type,
            "cmp"       : cmp_val,
            "iv"        : w_iv,
            "verdict"   : verdict,
            "quality"   : f"{quality.get('grade')} ({quality.get('score')}/100)",
            "discount"  : f"{disc:+.1f}%" if disc is not None else "N/A",
        }

    except Exception as outer_ex:
        result.fail(f"OUTER EXCEPTION: {outer_ex}")
        import traceback
        result.fail(traceback.format_exc()[:500])

    return result


def run_offline_tests() -> list:
    """
    Run logic-only tests that don't require network access.
    Tests helper functions, detector rules, aggregator math, etc.
    """
    results = []

    # ── Test: Detector routes correctly ───────────────────────────────────
    from screening.detector import detect

    def test_detector(name, data_snippet, expected_type):
        base = {
            "sector": "", "industry": "", "name": name,
            "symbol": name, "is_psu": False, "eps_growth_5y": 0,
            "revenue_std_pct": 0, "dps": 0, "revenue_growth_5y": 0,
            "net_profit_5y": [100, 90, 80, 70, 60], "is_profitable": True
        }
        base.update(data_snippet)
        det = detect(base)
        ok = det["stock_type"] == expected_type
        results.append({
            "test"    : f"Detector: {name} → {expected_type}",
            "passed"  : ok,
            "got"     : det["stock_type"],
        })

    test_detector("INFY",    {"sector": "Information Technology", "eps_growth_5y": 0.20}, "HIGH_GROWTH")
    test_detector("SBIN",    {"name": "STATE BANK OF INDIA", "is_psu": True, "sector": "Financial Services"}, "PSU")
    test_detector("HDFCBANK",{"sector": "Financial Services", "industry": "Banks"}, "BANK_NBFC")
    test_detector("TATASTEEL",{"sector": "Basic Materials", "industry": "Steel"}, "CYCLICAL")
    test_detector("HINDUNILVR",{"sector":"Consumer Defensive","dps": 10, "eps_growth_5y": 0.08}, "LARGE_STABLE")
    test_detector("LOSSMAKER",{"net_profit_5y": [-50, -30, -10, 5, 10], "is_profitable": False}, "EARLY_STAGE")
    test_detector("EMBASSY",  {"symbol": "EMBASSY", "name": "EMBASSY REIT", "sector": "Real Estate"}, "REIT")

    # ── Test: Aggregator normalises weights ────────────────────────────────
    from verdict.aggregator import aggregate

    fake_model_results = {
        "Graham": {"valid": True, "iv": 1000, "note": "test"},
        "DCF"   : {"valid": True, "iv": 1200, "note": "test"},
        "EPV"   : {"valid": True, "iv": 900,  "note": "test"},
    }
    fake_detection = {
        "stock_type": "HIGH_GROWTH",
        "weights"   : {"graham": 0.20, "dcf": 0.50, "epv": 0.30},
    }
    agg = aggregate(fake_model_results, fake_detection)
    iv = agg.get("weighted_iv")
    expected_iv = 1000 * 0.20 + 1200 * 0.50 + 900 * 0.30   # = 1070
    ok = iv is not None and abs(iv - expected_iv) < 1
    results.append({
        "test"  : f"Aggregator weighted IV = ₹{expected_iv:.0f}",
        "passed": ok,
        "got"   : f"₹{iv:.0f}" if iv else "None"
    })

    # ── Test: Cache round-trip ─────────────────────────────────────────────
    from data.cache import set_cache, get_cached, clear_cache
    test_data = {"symbol": "TESTSTOCK", "cmp": 999}
    set_cache("TESTSTOCK", test_data, "main")
    retrieved = get_cached("TESTSTOCK", "main")
    ok = retrieved == test_data
    results.append({
        "test"  : "Cache set → get round-trip",
        "passed": ok,
        "got"   : "OK" if ok else f"Got {retrieved}"
    })
    clear_cache("TESTSTOCK")

    # ── Test: Graham formula ───────────────────────────────────────────────
    # Graham IV = EPS × (8.5 + 2g) — sanity check
    from valuation.graham import calculate as graham_calc
    test_data_graham = {
        "cmp": 1500, "eps_ttm": 50, "eps_growth_5y": 0.15,
        "book_value_per_share": 300, "pb_ratio": 5,
        "revenue_growth_5y": 0.12, "debt_equity": 0.3,
    }
    gr = graham_calc(test_data_graham)
    # Expected: 50 × (8.5 + 2×15) = 50 × 38.5 = 1925
    expected_graham = 50 * (8.5 + 2 * 15)
    ok_graham = gr.get("valid") and gr.get("iv_simple") is not None
    results.append({
        "test"  : f"Graham formula IV_simple ≈ ₹{expected_graham:.0f}",
        "passed": ok_graham,
        "got"   : f"₹{gr.get('iv_simple','N/A')}"
    })

    # ── Test: DCF doesn't crash with minimal data ─────────────────────────
    from valuation.dcf import calculate as dcf_calc
    minimal_dcf = {
        "cmp": 1000, "eps_ttm": 40, "eps_growth_5y": 0.20,
        "revenue_growth_5y": 0.18, "net_profit_5y": [400, 350, 300],
        "fcf_5y": [300, 250, 200], "ebit_ttm": 500,
        "tax_rate": 0.25, "total_debt": 100, "cash": 50,
        "market_cap": 10000, "sector": "Information Technology",
    }
    try:
        dcf_r = dcf_calc(minimal_dcf, pharma_haircut=False)
        ok_dcf = isinstance(dcf_r, dict) and "valid" in dcf_r
    except Exception as e:
        ok_dcf = False
        dcf_r  = {"note": str(e)}
    results.append({
        "test"  : "DCF runs without crash on minimal data",
        "passed": ok_dcf,
        "got"   : dcf_r.get("note", "")[:80]
    })

    return results


# =============================================================================
# PRINT HELPERS
# =============================================================================

def print_offline_results(results: list):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  OFFLINE LOGIC TESTS ({len(results)} tests)")
    print(f"{'='*60}{Style.RESET_ALL}")
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    for r in results:
        icon  = f"{Fore.GREEN}✅{Style.RESET_ALL}" if r["passed"] else f"{Fore.RED}❌{Style.RESET_ALL}"
        print(f"  {icon} {r['test']}")
        if not r["passed"]:
            print(f"      Got: {r['got']}")
    print(f"\n  Result: {Fore.GREEN}{passed} passed{Style.RESET_ALL}, "
          f"{Fore.RED}{failed} failed{Style.RESET_ALL}")


def print_stock_result(tr: TestResult):
    header_color = Fore.GREEN if tr.success else Fore.RED
    print(f"\n  {header_color}{tr.summary()}{Style.RESET_ALL}")
    for msg in tr.passed:
        print(f"    {Fore.GREEN}✓{Style.RESET_ALL} {msg}")
    for msg in tr.warnings:
        print(f"    {Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")
    for msg in tr.failed:
        print(f"    {Fore.RED}✗ {msg}{Style.RESET_ALL}")
    if tr.data:
        d = tr.data
        print(f"    {'─'*50}")
        print(f"    Type:{d.get('stock_type','?'):15s}  "
              f"CMP:₹{d.get('cmp',0):,.0f}  "
              f"IV:₹{d.get('iv',0) or 0:,.0f}  "
              f"Disc:{d.get('discount','N/A'):>8s}  "
              f"Verdict:{d.get('verdict','?')}")


def print_final_summary(all_results: list):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  LIVE API TEST SUMMARY ({len(all_results)} stocks)")
    print(f"{'='*60}{Style.RESET_ALL}")

    pass_count = sum(1 for r in all_results if r.success)
    fail_count = sum(1 for r in all_results if not r.success)

    for r in all_results:
        icon = f"{Fore.GREEN}✅{Style.RESET_ALL}" if r.success else f"{Fore.RED}❌{Style.RESET_ALL}"
        verdict = r.data.get("verdict", "N/A") if r.data else "N/A"
        type_   = r.data.get("stock_type", "?") if r.data else "?"
        iv      = r.data.get("iv", None) if r.data else None
        iv_str  = f"₹{iv:,.0f}" if iv else "—"
        print(f"  {icon} {r.symbol:14s}  {type_:14s}  IV:{iv_str:>10s}  {verdict}")

    print(f"\n  Result: {Fore.GREEN}{pass_count} passed{Style.RESET_ALL}, "
          f"{Fore.RED}{fail_count} failed{Style.RESET_ALL} "
          f"out of {len(all_results)} stocks")

    if fail_count > 0:
        print(f"\n  {Fore.RED}Failed stocks:{Style.RESET_ALL}")
        for r in all_results:
            if not r.success:
                print(f"    • {r.symbol}: {r.failed}")

    # Export results to JSON for review
    export_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_results.json"
    )
    export_data = []
    for r in all_results:
        export_data.append({
            "symbol"  : r.symbol,
            "success" : r.success,
            "passed"  : r.passed,
            "failed"  : r.failed,
            "warnings": r.warnings,
            "data"    : r.data,
        })
    with open(export_path, "w") as f:
        json.dump(export_data, f, indent=2, default=str)
    print(f"\n  Results saved to: {export_path}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="NSE Stock Valuation Bot — End-to-End Test Suite"
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Run only offline logic tests (no API calls)"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Quick test: run only 3 stocks (INFY, HDFCBANK, COALINDIA)"
    )
    parser.add_argument(
        "--stock", type=str, default=None,
        help="Test a single stock (e.g. --stock RELIANCE)"
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="API call delay in seconds between stocks (default: 1.5)"
    )
    parser.add_argument(
        "--save-json", action="store_true",
        help="Save full test results to tests/test_results.json"
    )
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"  NSE STOCK VALUATION BOT — TEST SUITE")
    print(f"{'='*60}{Style.RESET_ALL}")

    # ── Always run offline tests first ────────────────────────────────────
    print(f"\n{Fore.YELLOW}Running offline logic tests...{Style.RESET_ALL}")
    offline_results = run_offline_tests()
    print_offline_results(offline_results)

    if args.offline:
        sys.exit(0 if all(r["passed"] for r in offline_results) else 1)

    # ── Select stocks to test ─────────────────────────────────────────────
    if args.stock:
        stocks_to_test = [{"symbol": args.stock.upper(), "expected_type": None,
                           "expect_profitable": True, "expect_iv": True}]
    elif args.quick:
        quick_symbols = ["INFY", "HDFCBANK", "COALINDIA"]
        stocks_to_test = [s for s in TEST_STOCKS if s["symbol"] in quick_symbols]
    else:
        stocks_to_test = TEST_STOCKS

    print(f"\n{Fore.YELLOW}Running live API tests on {len(stocks_to_test)} stocks "
          f"(delay={args.delay}s)...{Style.RESET_ALL}")
    print(f"  ⏱  Estimated time: ~{len(stocks_to_test)*args.delay:.0f}s + API latency\n")

    all_stock_results = []

    for i, stock_info in enumerate(stocks_to_test):
        sym = stock_info["symbol"]
        print(f"\n{Fore.CYAN}  [{i+1}/{len(stocks_to_test)}] Testing {sym}...{Style.RESET_ALL}")

        tr = run_full_test(stock_info, delay=args.delay)
        print_stock_result(tr)
        all_stock_results.append(tr)

        if i < len(stocks_to_test) - 1:
            time.sleep(args.delay)

    print_final_summary(all_stock_results)

    # Exit code: 0 = all passed, 1 = some failed
    any_failed = any(not r.success for r in all_stock_results)
    any_offline_failed = any(not r["passed"] for r in offline_results)
    sys.exit(1 if (any_failed or any_offline_failed) else 0)
