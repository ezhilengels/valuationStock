# =============================================================================
# screening/buffett_checklist.py — Warren Buffett Qualitative Checklist
#
# Separate from quality_filter.py (which handles quantitative numbers).
# This file handles MOAT and QUALITATIVE signals:
#
#   1. Pricing Power   — Can they raise prices without losing customers?
#   2. Switching Cost  — Is it painful to leave this company?
#   3. Network Effect  — Does value grow as more users join?
#   4. Cost Advantage  — Can they produce cheaper than all competitors?
#   5. Intangible Asset— Brand, patent, regulatory licence moat
#   6. Owner Operator  — Founder/promoter still running the business?
#   7. Capital Return  — Is management returning cash to shareholders?
#   8. Consistent ROE  — The ultimate moat test: ROE > 15% for 5+ years
#
# Output: WIDE MOAT / NARROW MOAT / NO MOAT + detailed signals
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Known moat companies (curated list — add your own) ───────────────────────
WIDE_MOAT_COMPANIES = {
    # FMCG — Brand moat
    "HINDUNILVR", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO",
    "COLPAL", "GODREJCP", "EMAMILTD", "TATACONSUM",
    # IT — Switching cost moat
    "TCS", "INFY", "HCLTECH", "WIPRO", "LTIM", "TECHM",
    # Specialty chemicals / paints — Cost + brand moat
    "ASIANPAINT", "BERGER", "KANSAINER", "PIDILITIND",
    # Financial — Network/scale moat
    "HDFCBANK", "KOTAKBANK", "BAJFINANCE",
    # Consumer brand — Pricing power
    "TITAN", "PAGEIND", "RELAXO",
    # Pharma — Patent / regulatory moat
    "SUNPHARMA", "DIVISLAB", "DRREDDY",
}

NARROW_MOAT_COMPANIES = {
    "ICICIBANK", "AXISBANK", "SBIN", "INDUSINDBK",
    "MARUTI", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT",
    "ITC", "HINDUNILVR", "BRITANNIA",
    "APOLLOHOSP", "MAXHEALTH", "FORTIS",
    "IRCTC", "CDSL", "BSE",   # Regulatory/network moats
}

# Sectors where moat is structurally strong
MOAT_SECTORS = {
    "Consumer Defensive" : "Brand pricing power — consumers loyal to brands",
    "Information Technology": "Switching cost — changing IT vendors is expensive/risky",
    "Technology"         : "Switching cost — changing IT vendors is expensive/risky",
    "Healthcare"         : "Regulatory/patent moat — drug approvals create barriers",
    "Pharmaceutical"     : "Regulatory/patent moat — drug approvals create barriers",
    "Financial Services" : "Scale/network moat — trust built over decades",
    "Utilities"          : "Regulatory moat — licensed monopolies in service areas",
}

# Sectors with structurally weak moats
COMMODITY_SECTORS = [
    "Basic Materials", "Steel", "Metals", "Aluminium",
    "Mining", "Oil & Gas", "Energy", "Chemicals",
]


def run(data: dict) -> dict:
    """
    Returns:
      {
        "moat_rating"    : str   (WIDE / NARROW / NO MOAT),
        "moat_score"     : int   (0-10),
        "signals_found"  : list  of positive moat signals,
        "red_flags"      : list  of moat-weakening signals,
        "buffett_score"  : int   (0-100 overall Buffett-style score),
        "buffett_grade"  : str   (A+ / A / B / C / D),
        "checklist"      : dict  of individual check results,
        "summary"        : str
      }
    """
    symbol   = (data.get("symbol") or "").replace(".NS", "").upper()
    name     = (data.get("name") or "").upper()
    sector   = data.get("sector") or ""
    industry = data.get("industry") or ""

    roe_list     = [r for r in (data.get("roe_5y") or []) if r is not None]
    gross_margins= [m for m in (data.get("gross_margin_5y") or []) if m is not None]
    rev_growth   = data.get("revenue_growth_5y") or 0
    eps_growth   = data.get("eps_growth_5y") or 0
    de_ratio     = data.get("debt_equity") or 0
    capex_ttm    = data.get("capex_ttm") or 0
    revenue_ttm  = data.get("revenue_ttm") or 1
    dps          = data.get("dps") or 0
    net_profit   = data.get("net_profit_ttm") or 0
    is_psu       = data.get("is_psu", False)
    mkt_cap      = data.get("market_cap") or 0

    signals    = []
    red_flags  = []
    checklist  = {}
    moat_score = 0

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1 — Pricing Power (Gross Margin > 40% consistently)
    # ─────────────────────────────────────────────────────────────────────────
    avg_gm = sum(gross_margins) / len(gross_margins) if gross_margins else None
    gm_consistent = sum(1 for m in gross_margins if m > 0.40) if gross_margins else 0

    if avg_gm and avg_gm > 0.50:
        signals.append(f"Strong pricing power (Gross Margin {avg_gm*100:.1f}% — above 50%)")
        moat_score += 2
        gm_result = "STRONG"
    elif avg_gm and avg_gm > 0.35:
        signals.append(f"Moderate pricing power (Gross Margin {avg_gm*100:.1f}%)")
        moat_score += 1
        gm_result = "MODERATE"
    elif avg_gm:
        red_flags.append(f"Low gross margin {avg_gm*100:.1f}% — limited pricing power")
        gm_result = "WEAK"
    else:
        gm_result = "N/A"

    checklist["pricing_power"] = {
        "name"  : "Pricing Power (Gross Margin > 40%)",
        "result": gm_result,
        "value" : f"{avg_gm*100:.1f}%" if avg_gm else "N/A",
        "detail": f"Consistent in {gm_consistent}/{len(gross_margins)} years" if gross_margins else "No data"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2 — Asset-Light Model (Capex/Revenue < 5%)
    # ─────────────────────────────────────────────────────────────────────────
    capex_intensity = capex_ttm / revenue_ttm if revenue_ttm > 0 else None

    if capex_intensity is not None:
        if capex_intensity < 0.03:
            signals.append(f"Asset-light business (Capex/Revenue {capex_intensity*100:.1f}%) — scalable model")
            moat_score += 2
            cap_result = "ASSET-LIGHT"
        elif capex_intensity < 0.08:
            cap_result = "MODERATE"
        else:
            red_flags.append(f"Capital-intensive (Capex/Revenue {capex_intensity*100:.1f}%) — harder to scale")
            cap_result = "CAPITAL-HEAVY"
    else:
        cap_result = "N/A"

    checklist["asset_light"] = {
        "name"  : "Asset-Light Model (Capex/Revenue < 5%)",
        "result": cap_result,
        "value" : f"{capex_intensity*100:.1f}%" if capex_intensity else "N/A",
        "detail": "Low capex = moat from intangibles or switching costs"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3 — Consistent ROE > 15% (The Buffett moat test)
    # ─────────────────────────────────────────────────────────────────────────
    roe_above_15 = sum(1 for r in roe_list if r > 0.15)
    avg_roe = sum(roe_list) / len(roe_list) if roe_list else 0

    if roe_list and roe_above_15 >= max(4, len(roe_list) - 1):
        signals.append(f"ROE consistently > 15% ({roe_above_15}/{len(roe_list)} years avg {avg_roe*100:.1f}%) — Buffett's #1 moat test")
        moat_score += 2
        roe_result = "CONSISTENT"
    elif roe_list and avg_roe > 0.15:
        signals.append(f"ROE above 15% average ({avg_roe*100:.1f}%) but inconsistent")
        moat_score += 1
        roe_result = "MODERATE"
    elif roe_list:
        red_flags.append(f"ROE below 15% average ({avg_roe*100:.1f}%) — no durable competitive advantage")
        roe_result = "WEAK"
    else:
        roe_result = "N/A"

    checklist["consistent_roe"] = {
        "name"  : "ROE > 15% Consistently (Buffett moat test)",
        "result": roe_result,
        "value" : f"{avg_roe*100:.1f}% avg",
        "detail": f"Above 15% in {roe_above_15}/{len(roe_list)} years"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4 — Known Moat Company (Curated List)
    # ─────────────────────────────────────────────────────────────────────────
    in_wide   = symbol in WIDE_MOAT_COMPANIES
    in_narrow = symbol in NARROW_MOAT_COMPANIES
    sec_moat  = MOAT_SECTORS.get(sector)

    if in_wide:
        signals.append(f"{symbol} is a known WIDE MOAT company (curated list)")
        moat_score += 2
        known_result = "WIDE MOAT"
    elif in_narrow:
        signals.append(f"{symbol} is a known NARROW MOAT company")
        moat_score += 1
        known_result = "NARROW MOAT"
    elif sec_moat:
        signals.append(f"Sector moat: {sec_moat}")
        moat_score += 1
        known_result = "SECTOR MOAT"
    else:
        known_result = "UNVERIFIED"

    checklist["known_moat"] = {
        "name"  : "Known Moat Company",
        "result": known_result,
        "value" : symbol,
        "detail": sec_moat or "Not in curated moat list — check manually"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5 — Commodity / No-Moat Sector Warning
    # ─────────────────────────────────────────────────────────────────────────
    in_commodity = any(s.lower() in sector.lower() for s in COMMODITY_SECTORS)
    if in_commodity and not in_wide:
        red_flags.append(f"Commodity sector ({sector}) — structurally difficult to build moat")
        moat_score = max(0, moat_score - 1)

    checklist["commodity_risk"] = {
        "name"  : "No Commodity Sector Risk",
        "result": "RISK" if in_commodity else "CLEAR",
        "value" : sector,
        "detail": "Commodity businesses rarely have durable pricing power"
                  if in_commodity else "Non-commodity sector"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6 — Capital Return to Shareholders
    # ─────────────────────────────────────────────────────────────────────────
    if dps > 0 and net_profit > 0:
        payout = (dps * (mkt_cap / (data.get("cmp") or 1))) / net_profit
        if payout > 0 and rev_growth > 0.10:
            signals.append(f"Growing dividends + revenue > 10% — capital allocation discipline")
            moat_score += 1
            cap_return = "GOOD"
        else:
            cap_return = "MODERATE"
    else:
        cap_return = "NO DIVIDEND"

    checklist["capital_return"] = {
        "name"  : "Capital Return to Shareholders",
        "result": cap_return,
        "value" : f"DPS ₹{dps:.1f}" if dps else "No dividend",
        "detail": "Consistent dividends + growth = disciplined management"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7 — PSU Moat Warning
    # ─────────────────────────────────────────────────────────────────────────
    if is_psu:
        red_flags.append("PSU — government policy risk, less management autonomy")
        checklist["psu_risk"] = {
            "name"  : "Management Autonomy",
            "result": "PSU RISK",
            "value" : "Government-owned",
            "detail": "Policy decisions can override business logic"
        }
    else:
        checklist["psu_risk"] = {
            "name"  : "Management Autonomy",
            "result": "PRIVATE",
            "value" : "Private company",
            "detail": "Management can act in shareholders' best interest"
        }

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8 — Revenue + EPS Growth Consistency
    # ─────────────────────────────────────────────────────────────────────────
    if rev_growth > 0.15 and eps_growth > 0.15:
        signals.append(f"Both revenue ({rev_growth*100:.1f}%) and EPS ({eps_growth*100:.1f}%) growing > 15% — strong growth moat")
        moat_score += 1
        growth_result = "STRONG"
    elif rev_growth > 0.08 and eps_growth > 0.08:
        growth_result = "MODERATE"
    else:
        red_flags.append(f"Low growth: Rev {rev_growth*100:.1f}%, EPS {eps_growth*100:.1f}%")
        growth_result = "WEAK"

    checklist["growth_moat"] = {
        "name"  : "Revenue + EPS Growth Consistency",
        "result": growth_result,
        "value" : f"Rev {rev_growth*100:.1f}% | EPS {eps_growth*100:.1f}%",
        "detail": "Sustained growth = expanding competitive advantage"
    }

    # ─────────────────────────────────────────────────────────────────────────
    # FINAL MOAT RATING
    # ─────────────────────────────────────────────────────────────────────────
    moat_score = min(moat_score, 10)

    if moat_score >= 7:
        moat_rating = "WIDE MOAT"
    elif moat_score >= 4:
        moat_rating = "NARROW MOAT"
    else:
        moat_rating = "NO MOAT / WEAK"

    # ─────────────────────────────────────────────────────────────────────────
    # BUFFETT OVERALL SCORE (0-100)
    # ─────────────────────────────────────────────────────────────────────────
    # Combines moat score (50%) + quantitative quality score from quality_filter (50%)
    buffett_score = int(moat_score / 10 * 100 * 0.5)

    # Add quantitative bonus
    if avg_roe > 0.20: buffett_score += 20
    elif avg_roe > 0.15: buffett_score += 12
    if de_ratio < 0.3:  buffett_score += 15
    elif de_ratio < 1.0: buffett_score += 8
    if rev_growth > 0.12: buffett_score += 10
    if not in_commodity: buffett_score += 5

    buffett_score = min(buffett_score, 100)

    if buffett_score >= 85: buffett_grade = "A+"
    elif buffett_score >= 75: buffett_grade = "A"
    elif buffett_score >= 60: buffett_grade = "B"
    elif buffett_score >= 45: buffett_grade = "C"
    else: buffett_grade = "D"

    # Summary
    summary = (
        f"{moat_rating} | Buffett Grade {buffett_grade} ({buffett_score}/100) | "
        f"{len(signals)} positive signals, {len(red_flags)} red flags"
    )

    return {
        "moat_rating"  : moat_rating,
        "moat_score"   : moat_score,
        "signals_found": signals,
        "red_flags"    : red_flags,
        "buffett_score": buffett_score,
        "buffett_grade": buffett_grade,
        "checklist"    : checklist,
        "summary"      : summary,
    }
