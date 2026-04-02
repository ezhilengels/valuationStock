# =============================================================================
# output/export.py — Excel Report Generator
# Creates a rich, colour-coded .xlsx report with multiple sheets:
#   Sheet 1: Summary (all stocks with verdict)
#   Sheet 2: Valuation Detail (all model IVs per stock)
#   Sheet 3: Quality Scorecard
#   Sheet 4: Relative Valuation
# =============================================================================

import os
from datetime import datetime
import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter


# ── Colour Palette ─────────────────────────────────────────────────────────
COLORS = {
    "header_bg"     : "1F3864",   # Dark navy
    "header_fg"     : "FFFFFF",   # White
    "strong_buy"    : "00B050",   # Dark green
    "buy"           : "92D050",   # Light green
    "hold"          : "FFEB9C",   # Yellow
    "overvalued"    : "FFC7CE",   # Light red
    "avoid"         : "FF0000",   # Red
    "early_stage"   : "FFEB9C",   # Yellow
    "pass_green"    : "C6EFCE",   # Light green
    "fail_red"      : "FFC7CE",   # Light red
    "partial_orange": "FFEB9C",   # Yellow
    "row_alt"       : "F2F2F2",   # Light grey for alternating rows
    "section_header": "D9E1F2",   # Light blue
    "cheap"         : "C6EFCE",
    "expensive"     : "FFC7CE",
    "fair"          : "FFFFFF",
    "subheader_bg"  : "2E75B6",   # Medium blue
}

VERDICT_COLORS = {
    "STRONG BUY"              : COLORS["strong_buy"],
    "BUY"                     : COLORS["buy"],
    "HOLD"                    : COLORS["hold"],
    "OVERVALUED"              : COLORS["overvalued"],
    "AVOID"                   : COLORS["avoid"],
    "EARLY STAGE — SPECULATIVE": COLORS["early_stage"],
}

QUALITY_COLORS = {
    "STRONG PASS": COLORS["strong_buy"],
    "PASS"       : COLORS["pass_green"],
    "PARTIAL"    : COLORS["partial_orange"],
    "FAIL"       : COLORS["fail_red"],
}


def export(results: list, output_path: str = None) -> str:
    """
    results: list of full result dicts from scanner/main, each containing:
      { symbol, name, cmp, iv, discount, verdict, quality, type,
        data, detection, quality_result, model_results, agg, decision }

    Returns: path to saved .xlsx file
    """
    if not output_path:
        ts          = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            f"valuation_report_{ts}.xlsx"
        )

    wb = openpyxl.Workbook()
    wb.remove(wb.active)   # Remove default sheet

    # ── Sheet 1: Executive Summary ─────────────────────────────────────────
    _build_summary_sheet(wb, results)

    # ── Sheet 2: Valuation Model Detail ───────────────────────────────────
    _build_valuation_sheet(wb, results)

    # ── Sheet 3: Quality Scorecard ────────────────────────────────────────
    _build_quality_sheet(wb, results)

    # ── Sheet 4: Relative Valuation ───────────────────────────────────────
    _build_relative_sheet(wb, results)

    wb.save(output_path)
    return output_path


# =============================================================================
# SHEET 1 — EXECUTIVE SUMMARY
# =============================================================================

def _build_summary_sheet(wb, results):
    ws = wb.create_sheet("Summary")
    ws.sheet_view.showGridLines = False

    # Title
    ws.merge_cells("A1:L1")
    ws["A1"] = f"NSE Stock Valuation Report — Generated {datetime.now().strftime('%d %b %Y %H:%M')}"
    _style(ws["A1"], bold=True, size=14, fg="FFFFFF", bg=COLORS["header_bg"],
           align="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells("A2:L2")
    ws["A2"] = "India Stock Valuation Bot | Graham + DCF + Lynch + Buffett + EPV + DDM + Excess Returns"
    _style(ws["A2"], size=9, fg="FFFFFF", bg=COLORS["subheader_bg"], align="center")
    ws.row_dimensions[2].height = 16

    # Headers Row 3
    headers = [
        "Ticker", "Company Name", "Sector / Type", "CMP (₹)",
        "Weighted IV (₹)", "Discount %", "IV Range (₹)",
        "Quality Grade", "Quality Score", "Peers", "Models Used", "VERDICT"
    ]
    col_widths = [14, 28, 22, 12, 16, 12, 20, 14, 13, 20, 30, 18]

    for col, (hdr, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=3, column=col, value=hdr)
        _style(cell, bold=True, fg="FFFFFF", bg=COLORS["header_bg"], align="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[3].height = 20

    # Freeze pane
    ws.freeze_panes = "A4"

    # Data rows
    sorted_results = sorted(
        [r for r in results if r],
        key=lambda x: x.get("discount") or -999,
        reverse=True
    )

    for row_idx, r in enumerate(sorted_results, 4):
        is_alt   = (row_idx % 2 == 0)
        row_bg   = COLORS["row_alt"] if is_alt else "FFFFFF"
        verdict  = r.get("verdict", "N/A")
        v_color  = VERDICT_COLORS.get(verdict, "FFFFFF")
        q_grade  = r.get("quality", "N/A")
        q_color  = QUALITY_COLORS.get(q_grade, "FFFFFF")
        discount = r.get("discount")
        iv       = r.get("iv")
        cmp      = r.get("cmp")

        # IV range
        agg      = r.get("agg", {})
        iv_lo, iv_hi = agg.get("iv_range", (None, None))
        iv_range = (f"₹{iv_lo:,.0f} – ₹{iv_hi:,.0f}"
                    if iv_lo and iv_hi else "N/A")

        # Models used
        detection   = r.get("detection", {})
        models_used = ", ".join(detection.get("models_to_use", []))

        # Peers
        rel = (r.get("model_results") or {}).get("Relative", {})
        peers = (rel or {}).get("overall_relative", "N/A")

        row_data = [
            r.get("symbol", ""),
            r.get("name", ""),
            f"{r.get('type', 'N/A')} / {(r.get('data') or {}).get('sector', '')}",
            cmp,
            iv,
            f"{discount:+.1f}%" if discount is not None else "N/A",
            iv_range,
            q_grade,
            r.get("quality_result", {}).get("score", "N/A"),
            peers,
            models_used,
            verdict,
        ]

        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            _style(cell, bg=row_bg)

            # Special formatting
            if col == 4 and cmp:          # CMP
                cell.number_format = '₹#,##0.00'
            if col == 5 and iv:           # IV
                cell.number_format = '₹#,##0.00'
                iv_color = (COLORS["strong_buy"] if iv > (cmp or 0) * 1.3
                            else COLORS["buy"] if iv > (cmp or 0)
                            else COLORS["fail_red"])
                _style(cell, bg=iv_color, bold=True)
            if col == 6 and discount is not None:   # Discount
                disc_color = (COLORS["strong_buy"] if discount >= 30
                              else COLORS["buy"] if discount >= 15
                              else COLORS["hold"] if discount >= 0
                              else COLORS["fail_red"])
                _style(cell, bg=disc_color, bold=True, align="center")
            if col == 8:   # Quality Grade
                _style(cell, bg=q_color, align="center")
            if col == 9:   # Quality Score
                score = r.get("quality_result", {}).get("score", 0)
                s_color = (COLORS["strong_buy"] if score >= 80
                           else COLORS["buy"] if score >= 60
                           else COLORS["hold"] if score >= 40
                           else COLORS["fail_red"])
                _style(cell, bg=s_color, align="center")
            if col == 10:  # Peers
                p_color = (COLORS["cheap"] if "CHEAP" in str(peers)
                           else COLORS["expensive"] if "EXPENSIVE" in str(peers)
                           else "FFFFFF")
                _style(cell, bg=p_color)
            if col == 12:  # Verdict
                _style(cell, bg=v_color, bold=True, align="center", size=10)

        ws.row_dimensions[row_idx].height = 18

    # Auto-filter
    ws.auto_filter.ref = f"A3:L{3 + len(sorted_results)}"


# =============================================================================
# SHEET 2 — VALUATION MODEL DETAIL
# =============================================================================

def _build_valuation_sheet(wb, results):
    ws = wb.create_sheet("Valuation Detail")
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:K1")
    ws["A1"] = "Intrinsic Value by Model"
    _style(ws["A1"], bold=True, size=13, fg="FFFFFF",
           bg=COLORS["header_bg"], align="center")
    ws.row_dimensions[1].height = 24

    model_cols = [
        "Graham (Simple)", "Graham (Adjusted)", "DCF",
        "Lynch", "Buffett OE", "EPV", "DDM",
        "Excess Returns", "EV/Sales", "Mid-Cycle EV"
    ]
    headers = ["Ticker", "CMP (₹)", "Weighted IV (₹)", "Discount %"] + model_cols + ["Confidence"]
    widths  = [14, 12, 14, 12] + [16] * len(model_cols) + [14]

    for col, (hdr, width) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=2, column=col, value=hdr)
        _style(cell, bold=True, fg="FFFFFF", bg=COLORS["subheader_bg"], align="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A3"

    MODEL_RESULT_KEYS = {
        "Graham (Simple)"  : ("Graham",        "iv_simple"),
        "Graham (Adjusted)": ("Graham",        "iv_adjusted"),
        "DCF"              : ("DCF",           "iv"),
        "Lynch"            : ("Lynch",         "iv"),
        "Buffett OE"       : ("Buffett",       "iv"),
        "EPV"              : ("EPV",           "iv"),
        "DDM"              : ("DDM",           "iv"),
        "Excess Returns"   : ("ExcessReturns", "iv"),
        "EV/Sales"         : ("EV/Sales",      "iv"),
        "Mid-Cycle EV"     : ("MidCycleEV",   "iv"),
    }

    for row_idx, r in enumerate(
        sorted([x for x in results if x], key=lambda x: x.get("discount") or -999, reverse=True),
        3
    ):
        is_alt = (row_idx % 2 == 0)
        bg = COLORS["row_alt"] if is_alt else "FFFFFF"
        cmp = r.get("cmp")
        iv  = r.get("iv")
        disc= r.get("discount")
        model_results = r.get("model_results") or {}
        agg = r.get("agg") or {}

        row_vals = [
            r.get("symbol", ""),
            cmp,
            iv,
            f"{disc:+.1f}%" if disc is not None else "N/A",
        ]

        for col_name in model_cols:
            result_key, field = MODEL_RESULT_KEYS[col_name]
            model_r = model_results.get(result_key)
            if model_r and model_r.get("valid") and model_r.get(field) is not None:
                row_vals.append(model_r[field])
            else:
                row_vals.append("—")

        row_vals.append(agg.get("confidence", "N/A"))

        for col, val in enumerate(row_vals, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            _style(cell, bg=bg, align="center")
            if col in [2, 3] and isinstance(val, (int, float)):
                cell.number_format = '₹#,##0.00'
            # Colour IV columns green if > CMP, red if < CMP
            if col >= 5 and isinstance(val, (int, float)) and cmp:
                iv_color = (COLORS["buy"] if val > cmp else
                            COLORS["fail_red"] if val < cmp * 0.9 else bg)
                _style(cell, bg=iv_color)
                cell.number_format = '₹#,##0.00'

        ws.row_dimensions[row_idx].height = 18


# =============================================================================
# SHEET 3 — QUALITY SCORECARD
# =============================================================================

def _build_quality_sheet(wb, results):
    ws = wb.create_sheet("Quality Scorecard")
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:L1")
    ws["A1"] = "Quality Scorecard — Buffett Checklist"
    _style(ws["A1"], bold=True, size=13, fg="FFFFFF",
           bg=COLORS["header_bg"], align="center")
    ws.row_dimensions[1].height = 24

    check_cols = [
        "ROE > 15%", "Profitable", "OCF Quality", "D/E < 1",
        "Int. Cover", "Curr Ratio", "Rev Growth", "EPS Growth",
        "FCF Consistency", "Gross Margin"
    ]
    headers = ["Ticker", "Grade", "Score /100", "Moat Signals"] + check_cols
    widths  = [14, 14, 12, 35] + [14] * len(check_cols)

    for col, (hdr, width) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=2, column=col, value=hdr)
        _style(cell, bold=True, fg="FFFFFF", bg=COLORS["subheader_bg"], align="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A3"

    CHECK_KEYS = [
        "roe", "profitable", "ocf_quality", "debt_equity",
        "interest_coverage", "current_ratio", "revenue_growth",
        "eps_growth", "fcf_consistency", "gross_margin"
    ]

    for row_idx, r in enumerate([x for x in results if x], 3):
        is_alt = (row_idx % 2 == 0)
        bg = COLORS["row_alt"] if is_alt else "FFFFFF"
        qr = r.get("quality_result") or {}
        grade  = qr.get("grade", "N/A")
        score  = qr.get("score", 0)
        checks = qr.get("checks", {})
        moats  = " | ".join(qr.get("moat_flags", []))
        q_color= QUALITY_COLORS.get(grade, bg)

        row_vals = [r.get("symbol", ""), grade, score, moats]

        for ck in CHECK_KEYS:
            check = checks.get(ck)
            if check is None:
                row_vals.append("N/A")
            else:
                passed = check.get("pass")
                val    = check.get("value", "N/A")
                row_vals.append(val)

        for col, val in enumerate(row_vals, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            _style(cell, bg=bg, align="center")

            if col == 2:  # Grade
                _style(cell, bg=q_color, bold=True, align="center")
            if col == 3:  # Score
                s_color = (COLORS["strong_buy"] if score >= 80
                           else COLORS["buy"] if score >= 60
                           else COLORS["hold"] if score >= 40
                           else COLORS["fail_red"])
                _style(cell, bg=s_color, bold=True, align="center")
            if col == 4:  # Moats
                _style(cell, align="left")
            if col >= 5:  # Check columns
                ck      = CHECK_KEYS[col - 5]
                check   = checks.get(ck)
                if check:
                    passed  = check.get("pass")
                    ck_color= (COLORS["pass_green"] if passed
                               else COLORS["fail_red"] if passed is False
                               else bg)
                    _style(cell, bg=ck_color, align="center")

        ws.row_dimensions[row_idx].height = 18


# =============================================================================
# SHEET 4 — RELATIVE VALUATION
# =============================================================================

def _build_relative_sheet(wb, results):
    ws = wb.create_sheet("Relative Valuation")
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:J1")
    ws["A1"] = "Relative Valuation vs Sector Peers"
    _style(ws["A1"], bold=True, size=13, fg="FFFFFF",
           bg=COLORS["header_bg"], align="center")
    ws.row_dimensions[1].height = 24

    headers = [
        "Ticker", "Sector", "P/E", "Sector P/E", "P/E Status",
        "P/B", "Sector P/B", "P/B Status",
        "EV/EBITDA", "Sector EV/EBITDA", "EV/EBITDA Status",
        "PEG", "Overall vs Peers"
    ]
    widths = [14, 22, 10, 12, 14, 10, 12, 14, 12, 18, 18, 10, 20]

    for col, (hdr, width) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=2, column=col, value=hdr)
        _style(cell, bold=True, fg="FFFFFF", bg=COLORS["subheader_bg"], align="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.freeze_panes = "A3"

    STATUS_COLORS = {
        "CHEAP"    : COLORS["cheap"],
        "FAIR"     : "FFFFFF",
        "EXPENSIVE": COLORS["expensive"],
    }

    for row_idx, r in enumerate([x for x in results if x], 3):
        is_alt  = (row_idx % 2 == 0)
        bg      = COLORS["row_alt"] if is_alt else "FFFFFF"
        rel     = (r.get("model_results") or {}).get("Relative") or {}
        metrics = rel.get("metrics", {})
        bmarks  = rel.get("sector_medians", {})
        comps   = rel.get("comparisons", {})
        overall = rel.get("overall_relative", "N/A")
        sector  = (r.get("data") or {}).get("sector", "N/A")

        def _status(key):
            return comps.get(key, {}).get("status", "N/A")

        row_data = [
            r.get("symbol", ""), sector,
            metrics.get("pe"),       bmarks.get("pe"),       _status("pe"),
            metrics.get("pb"),       bmarks.get("pb"),       _status("pb"),
            metrics.get("ev_ebitda"),bmarks.get("ev_ebitda"),_status("ev_ebitda"),
            metrics.get("peg"),
            overall,
        ]

        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col, value=val)
            _style(cell, bg=bg, align="center")

            # Colour status columns
            if col in [5, 8, 11]:  # Status columns
                s_color = STATUS_COLORS.get(str(val), bg)
                _style(cell, bg=s_color, bold=True, align="center")
            if col == 13:  # Overall
                ov_color = (COLORS["cheap"] if "CHEAP" in str(val)
                            else COLORS["expensive"] if "EXPENSIVE" in str(val)
                            else bg)
                _style(cell, bg=ov_color, bold=True, align="center")
            if col in [3, 4, 6, 7, 9, 10, 12] and isinstance(val, float):
                cell.number_format = '0.0'

        ws.row_dimensions[row_idx].height = 18


# =============================================================================
# STYLE HELPERS
# =============================================================================

def _style(cell, bold=False, size=10, fg="000000", bg=None,
           align="left", wrap=False):
    cell.font      = Font(bold=bold, size=size, color=fg)
    cell.alignment = Alignment(
        horizontal=align, vertical="center", wrap_text=wrap
    )
    if bg:
        cell.fill = PatternFill(fill_type="solid", fgColor=bg)
    cell.border = Border(
        bottom=Side(style="thin", color="D9D9D9")
    )


def _thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)
