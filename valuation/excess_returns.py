# =============================================================================
# valuation/excess_returns.py — Excess Returns Model (Banks / NBFCs)
#
# Value = Book Value + PV of (ROE − Cost of Equity) × Book Value
#
# If ROE > CoE → stock deserves premium to book
# If ROE < CoE → stock deserves discount to book
#
# Cost of Equity = Risk-free Rate + Beta × Equity Risk Premium
#                = G-Sec yield + Beta × 5%
# =============================================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    get_discount_rate, GSEC_10Y_YIELD, EQUITY_RISK_PREMIUM,
    BETA_LARGE_BANK, TERMINAL_GROWTH_RATE
)


def calculate(data: dict) -> dict:
    """
    Returns:
      {
        "model"           : "ExcessReturns",
        "iv"              : float or None,
        "book_value_ps"   : float,
        "current_roe"     : float,
        "cost_of_equity"  : float,
        "excess_return"   : float,
        "justified_pb"    : float,   # what P/B ratio the ROE justifies
        "current_pb"      : float,
        "pb_verdict"      : str,
        "inputs_used"     : dict,
        "note"            : str,
        "valid"           : bool
      }
    """
    bvps    = data.get("book_value_per_share")
    roe_list= data.get("roe_5y") or []
    beta    = data.get("beta") or BETA_LARGE_BANK
    pb      = data.get("pb_ratio")
    cmp     = data.get("cmp")
    g_rate  = data.get("eps_growth_5y") or TERMINAL_GROWTH_RATE

    # ── Validation ─────────────────────────────────────────────────────────
    if not bvps or bvps <= 0:
        return _invalid("Book Value per share missing — Excess Returns not applicable")

    roe_vals = [r for r in roe_list if r is not None]
    if not roe_vals:
        return _invalid("ROE data unavailable — Excess Returns not applicable")

    # Use 3Y average ROE for stability
    avg_roe = sum(roe_vals[:3]) / len(roe_vals[:3])

    # ── Cost of Equity (CAPM) ──────────────────────────────────────────────
    coe = get_discount_rate(beta)

    # ── Excess Return ──────────────────────────────────────────────────────
    excess_return = avg_roe - coe   # Positive = value creation
    g             = min(g_rate, coe * 0.8)   # Growth must be < CoE

    # ── Intrinsic Value ────────────────────────────────────────────────────
    # IV = BV + BV × (ROE - CoE) / (CoE - g)    [if CoE > g]
    if coe <= g:
        g = coe * 0.5

    if coe - g > 0:
        iv = bvps + bvps * (excess_return / (coe - g))
    else:
        iv = bvps   # Fallback to book value if formula breaks

    iv = max(iv, 0)   # Cannot be negative

    # ── Justified P/B ─────────────────────────────────────────────────────
    # Justified P/B = IV / BVPS = 1 + (ROE - CoE) / (CoE - g)
    justified_pb = iv / bvps if bvps > 0 else None

    # ── P/B Verdict ───────────────────────────────────────────────────────
    current_pb = pb or (cmp / bvps if cmp and bvps else None)
    if current_pb and justified_pb:
        if current_pb < justified_pb * 0.85:
            pb_verdict = f"UNDERVALUED (P/B {current_pb:.1f}x < Justified {justified_pb:.1f}x)"
        elif current_pb > justified_pb * 1.15:
            pb_verdict = f"OVERVALUED (P/B {current_pb:.1f}x > Justified {justified_pb:.1f}x)"
        else:
            pb_verdict = f"FAIRLY VALUED (P/B {current_pb:.1f}x ≈ Justified {justified_pb:.1f}x)"
    else:
        pb_verdict = "N/A"

    if excess_return > 0:
        note = f"ROE ({avg_roe*100:.1f}%) > CoE ({coe*100:.1f}%) → Stock justifies premium to book"
    else:
        note = f"ROE ({avg_roe*100:.1f}%) < CoE ({coe*100:.1f}%) → Stock should trade below book"

    return {
        "model"          : "ExcessReturns",
        "iv"             : round(iv, 2),
        "book_value_ps"  : round(bvps, 2),
        "current_roe"    : round(avg_roe * 100, 2),
        "cost_of_equity" : round(coe * 100, 2),
        "excess_return"  : round(excess_return * 100, 2),
        "justified_pb"   : round(justified_pb, 2) if justified_pb else None,
        "current_pb"     : round(current_pb, 2) if current_pb else None,
        "pb_verdict"     : pb_verdict,
        "inputs_used"    : {
            "bvps"         : bvps,
            "avg_roe"      : f"{avg_roe*100:.1f}%",
            "beta"         : beta,
            "gsec_yield"   : f"{GSEC_10Y_YIELD*100:.1f}%",
            "erp"          : f"{EQUITY_RISK_PREMIUM*100:.1f}%",
            "cost_of_eq"   : f"{coe*100:.2f}%",
            "growth_used"  : f"{g*100:.1f}%",
        },
        "note"  : note,
        "valid" : True
    }


def _invalid(reason: str) -> dict:
    return {
        "model": "ExcessReturns", "iv": None,
        "book_value_ps": None, "current_roe": None,
        "cost_of_equity": None, "excess_return": None,
        "justified_pb": None, "current_pb": None,
        "pb_verdict": "N/A",
        "inputs_used": {}, "note": reason, "valid": False
    }
