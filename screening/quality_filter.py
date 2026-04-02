# =============================================================================
# screening/quality_filter.py — Buffett Quality Gate
#
# Checks before any valuation runs:
#   PROFITABILITY: ROE, Net Margin, OCF quality
#   SAFETY:        D/E, Interest Coverage, Current Ratio
#   GROWTH:        Revenue CAGR, EPS CAGR, FCF consistency
#   MOAT PROXIES:  Gross Margin, ROE consistency, Asset-lightness
#
# Output: STRONG PASS / PASS / PARTIAL / FAIL
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MIN_ROE, MAX_DEBT_EQUITY, MIN_REVENUE_GROWTH,
    MIN_INTEREST_COVERAGE, MIN_CURRENT_RATIO,
    MIN_GROSS_MARGIN, MIN_FCF_POSITIVE_YEARS
)
from data.cleaner import avg_roe, avg_gross_margin


def run(data: dict) -> dict:
    """
    Returns:
      {
        "score"       : int (0-100),
        "grade"       : str (STRONG PASS / PASS / PARTIAL / FAIL),
        "checks"      : dict of individual check results,
        "passed"      : list of passed checks,
        "failed"      : list of failed checks,
        "moat_score"  : int (0-3),
        "moat_flags"  : list of moat signals found
      }
    """
    checks  = {}
    passed  = []
    failed  = []

    # ─────────────────────────────────────────────────────────────────────
    # PROFITABILITY CHECKS
    # ─────────────────────────────────────────────────────────────────────

    # 1. ROE > 15% consistently
    roe_list = [r for r in (data.get("roe_5y") or []) if r is not None]
    avg_roe_val = sum(roe_list) / len(roe_list) if roe_list else 0
    roe_consistent = sum(1 for r in roe_list if r >= MIN_ROE)
    roe_pass = avg_roe_val >= MIN_ROE and roe_consistent >= max(1, len(roe_list) // 2)

    checks["roe"] = {
        "name"   : "ROE > 15% (avg)",
        "value"  : f"{avg_roe_val*100:.1f}%",
        "target" : f"> {MIN_ROE*100:.0f}%",
        "pass"   : roe_pass,
        "detail" : f"Avg ROE: {avg_roe_val*100:.1f}%, consistent in {roe_consistent}/{len(roe_list)} years"
    }
    (passed if roe_pass else failed).append("ROE")

    # 2. Positive profitability (not loss-making)
    is_profitable = data.get("is_profitable", True)
    checks["profitable"] = {
        "name"   : "Consistently Profitable",
        "value"  : "Yes" if is_profitable else "No",
        "target" : "Profit in 2+ of last 3 years",
        "pass"   : is_profitable,
        "detail" : "" if is_profitable else "Loss-making — quality gate concern"
    }
    (passed if is_profitable else failed).append("Profitability")

    # 3. OCF > Net Profit (earnings quality check)
    ocf_list = data.get("operating_cf_5y") or []
    np_list  = data.get("net_profit_5y") or []
    if ocf_list and np_list:
        ocf_beats = sum(
            1 for ocf, np in zip(ocf_list, np_list)
            if ocf is not None and np is not None and ocf > np
        )
        ocf_pass = ocf_beats >= max(1, len(ocf_list) // 2)
        ocf_detail = f"OCF > Net Profit in {ocf_beats}/{len(ocf_list)} years"
    else:
        ocf_pass   = None   # Insufficient data
        ocf_detail = "Insufficient cash flow data"

    checks["ocf_quality"] = {
        "name"   : "OCF > Net Profit (earnings quality)",
        "value"  : ocf_detail,
        "target" : "OCF > Net Profit in majority of years",
        "pass"   : ocf_pass,
        "detail" : ocf_detail
    }
    if ocf_pass is not None:
        (passed if ocf_pass else failed).append("OCF Quality")

    # ─────────────────────────────────────────────────────────────────────
    # SAFETY CHECKS
    # ─────────────────────────────────────────────────────────────────────

    # 4. Debt / Equity < 1
    de = data.get("debt_equity")
    de_pass = de is not None and de <= MAX_DEBT_EQUITY
    checks["debt_equity"] = {
        "name"   : "Debt/Equity < 1.0",
        "value"  : f"{de:.2f}" if de is not None else "N/A",
        "target" : f"< {MAX_DEBT_EQUITY}",
        "pass"   : de_pass,
        "detail" : f"D/E = {de:.2f}" if de is not None else "D/E data unavailable"
    }
    if de is not None:
        (passed if de_pass else failed).append("Debt/Equity")

    # 5. Interest Coverage > 3x
    ic = data.get("interest_coverage")
    ic_pass = ic is not None and ic >= MIN_INTEREST_COVERAGE
    checks["interest_coverage"] = {
        "name"   : "Interest Coverage > 3x",
        "value"  : f"{ic:.1f}x" if ic and ic < 999 else ("∞ (no debt)" if ic == 999 else "N/A"),
        "target" : f"> {MIN_INTEREST_COVERAGE}x",
        "pass"   : ic_pass,
        "detail" : f"EBIT covers interest {ic:.1f}x" if ic and ic < 999 else "No debt"
    }
    if ic is not None:
        (passed if ic_pass else failed).append("Interest Coverage")

    # 6. Current Ratio > 1.5
    cr = data.get("current_ratio")
    cr_pass = cr is not None and cr >= MIN_CURRENT_RATIO
    checks["current_ratio"] = {
        "name"   : "Current Ratio > 1.5",
        "value"  : f"{cr:.2f}" if cr else "N/A",
        "target" : f"> {MIN_CURRENT_RATIO}",
        "pass"   : cr_pass if cr else None,
        "detail" : f"Current ratio: {cr:.2f}" if cr else "Data unavailable"
    }
    if cr:
        (passed if cr_pass else failed).append("Current Ratio")

    # ─────────────────────────────────────────────────────────────────────
    # GROWTH CHECKS
    # ─────────────────────────────────────────────────────────────────────

    # 7. Revenue CAGR > 10%
    rev_g = data.get("revenue_growth_5y")
    rev_pass = rev_g is not None and rev_g >= MIN_REVENUE_GROWTH
    checks["revenue_growth"] = {
        "name"   : "Revenue CAGR > 10% (5Y)",
        "value"  : f"{rev_g*100:.1f}%" if rev_g else "N/A",
        "target" : f"> {MIN_REVENUE_GROWTH*100:.0f}%",
        "pass"   : rev_pass,
        "detail" : f"5Y Revenue CAGR: {rev_g*100:.1f}%" if rev_g else "Data unavailable"
    }
    if rev_g is not None:
        (passed if rev_pass else failed).append("Revenue Growth")

    # 8. EPS CAGR > 10%
    eps_g = data.get("eps_growth_5y")
    eps_pass = eps_g is not None and eps_g >= MIN_REVENUE_GROWTH
    checks["eps_growth"] = {
        "name"   : "EPS CAGR > 10% (5Y)",
        "value"  : f"{eps_g*100:.1f}%" if eps_g else "N/A",
        "target" : "> 10%",
        "pass"   : eps_pass,
        "detail" : f"5Y EPS CAGR: {eps_g*100:.1f}%" if eps_g else "Data unavailable"
    }
    if eps_g is not None:
        (passed if eps_pass else failed).append("EPS Growth")

    # 9. Positive FCF in 3+ of last 5 years
    fcf_list = data.get("fcf_5y") or []
    fcf_vals = [v for v in fcf_list if v is not None]
    fcf_positive = sum(1 for v in fcf_vals if v > 0)
    fcf_pass = fcf_positive >= MIN_FCF_POSITIVE_YEARS
    checks["fcf_consistency"] = {
        "name"   : "FCF Positive in 3+ of 5 years",
        "value"  : f"{fcf_positive}/{len(fcf_vals)} years",
        "target" : f">= {MIN_FCF_POSITIVE_YEARS} years positive",
        "pass"   : fcf_pass if fcf_vals else None,
        "detail" : f"Positive FCF in {fcf_positive} of {len(fcf_vals)} available years"
    }
    if fcf_vals:
        (passed if fcf_pass else failed).append("FCF Consistency")

    # ─────────────────────────────────────────────────────────────────────
    # MOAT PROXIES
    # ─────────────────────────────────────────────────────────────────────
    moat_flags = []

    # Moat 1: Gross Margin > 40% → Pricing power
    gm = avg_gross_margin(data)
    if gm is not None:
        if gm >= MIN_GROSS_MARGIN:
            moat_flags.append(f"Pricing Power (Gross Margin {gm*100:.1f}% > 40%)")
        checks["gross_margin"] = {
            "name"   : "Gross Margin > 40% (moat)",
            "value"  : f"{gm*100:.1f}%",
            "target" : "> 40%",
            "pass"   : gm >= MIN_GROSS_MARGIN,
            "detail" : f"Avg Gross Margin: {gm*100:.1f}%"
        }
        (passed if gm >= MIN_GROSS_MARGIN else failed).append("Gross Margin")

    # Moat 2: ROE consistently > 15% over 5 years → Competitive advantage
    if roe_consistent >= 4 and len(roe_list) >= 4:
        moat_flags.append(f"Consistent ROE > 15% ({roe_consistent} of {len(roe_list)} years)")

    # Moat 3: Asset-light (low capex vs revenue)
    capex   = data.get("capex_ttm") or 0
    revenue = data.get("revenue_ttm") or 1
    capex_intensity = capex / revenue if revenue > 0 else None
    if capex_intensity is not None and capex_intensity < 0.05:
        moat_flags.append(f"Asset-Light Model (Capex/Revenue: {capex_intensity*100:.1f}%)")

    moat_score = len(moat_flags)

    # ─────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────
    total_checks    = len(passed) + len(failed)
    score           = int(len(passed) / total_checks * 100) if total_checks > 0 else 0
    score          += moat_score * 5   # Bonus for moat signals
    score           = min(score, 100)

    if score >= 80:
        grade = "STRONG PASS"
    elif score >= 60:
        grade = "PASS"
    elif score >= 40:
        grade = "PARTIAL"
    else:
        grade = "FAIL"

    return {
        "score"     : score,
        "grade"     : grade,
        "checks"    : checks,
        "passed"    : passed,
        "failed"    : failed,
        "moat_score": moat_score,
        "moat_flags": moat_flags
    }
