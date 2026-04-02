# =============================================================================
# buffett_report.py — Institutional-Grade Stock Research Report
# Standalone UI focused on Quality (Buffett) and Fair Value
#
# Run:  python3 -m streamlit run buffett_report.py
# =============================================================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os
import time
from typing import Union, List, Dict, Tuple

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config as cfg
from data.fetcher import fetch_stock_data, fetch_gsec_yield
from data.cleaner import clean, validate
from screening.detector import detect
from screening.buffett_checklist import run as run_buffett_check
from screening.quality_filter import run as run_quality_filter
from valuation import (
    graham, dcf, lynch, buffett, epv, ddm,
    excess_returns, ev_sales, mid_cycle, nav, price_tam, relative
)
from verdict.aggregator import aggregate
from verdict.decision import decide

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Buffett Research Report",
    page_icon="🧐",
    layout="wide"
)

# ── CUSTOM CSS FOR INSTITUTIONAL LOOK ─────────────────────────────────────────
st.markdown("""
<style>
    .report-title { font-size: 32px; font-weight: 800; color: #1F3864; margin-bottom: 0; }
    .report-subtitle { font-size: 16px; color: #5B9BD5; margin-bottom: 20px; }
    
    /* Hero Badge Styles */
    .verdict-hero {
        padding: 20px; border-radius: 12px; text-align: center;
        font-weight: bold; font-size: 28px; margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .hero-STRONG-BUY { background-color: #00B050; color: white; }
    .hero-BUY { background-color: #92D050; color: #1a1a1a; }
    .hero-HOLD { background-color: #FFEB9C; color: #1a1a1a; }
    .hero-OVERVALUED { background-color: #FFC7CE; color: #9C0006; }
    .hero-AVOID { background-color: #FF4444; color: white; }
    
    /* Buffett Grid Card Styles */
    .buffett-card {
        padding: 15px; border-radius: 10px; border: 1px solid #dee2e6;
        height: 140px; text-align: center; margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .buffett-card:hover { transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .card-title { font-size: 13px; font-weight: 600; color: #666; margin-bottom: 8px; text-transform: uppercase; }
    .card-value { font-size: 20px; font-weight: 700; margin-bottom: 5px; }
    .card-status { font-size: 12px; font-weight: 800; padding: 2px 8px; border-radius: 4px; }
    
    .status-PASS { background-color: #C6EFCE; color: #006100; }
    .status-FAIL { background-color: #FFC7CE; color: #9C0006; }
    .status-MARGINAL { background-color: #FFEB9C; color: #9C6500; }
    .status-NA { background-color: #f8f9fa; color: #6c757d; }

    /* Section Headers */
    .section-header {
        font-size: 18px; font-weight: 700; color: #1F3864;
        border-bottom: 3px solid #2E75B6; padding-bottom: 5px;
        margin: 25px 0 15px 0; display: flex; align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ── DATA PIPELINE ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_full_report(symbol: str) -> Union[dict, None]:
    """Execute the entire institutional valuation engine."""
    # 1. Fetch
    raw_data = fetch_stock_data(symbol)
    if not raw_data: return None
    
    # 2. Clean & Validate
    data = clean(raw_data)
    is_ok, warnings = validate(data)
    if not is_ok: return None
    
    # 3. Detect & Filter
    detection = detect(data)
    quality   = run_quality_filter(data)
    buffett_chk = run_buffett_check(data)
    
    # 4. Valuation Models
    models = detection.get("models_to_use", [])
    results = {}
    
    # Compute all available models
    results["Graham"]        = graham.calculate(data)
    results["DCF"]           = dcf.calculate(data, pharma_haircut=("pharma" in (data.get("sector") or "").lower()))
    results["Lynch"]         = lynch.calculate(data)
    results["Buffett"]       = buffett.calculate(data)
    results["EPV"]           = epv.calculate(data)
    results["DDM"]           = ddm.calculate(data)
    results["ExcessReturns"] = excess_returns.calculate(data)
    results["EV/Sales"]      = ev_sales.calculate(data)
    results["MidCycleEV"]    = mid_cycle.calculate(data)
    results["NAV"]           = nav.calculate(data)
    results["PriceTAM"]      = price_tam.calculate(data)
    results["Relative"]      = relative.calculate(data)
    
    # 5. Aggregate & Decide
    agg = aggregate(results, detection)
    decision = decide(data.get("cmp"), agg, quality, results["Relative"], detection)
    
    return {
        "data": data, "detection": detection, "quality": quality,
        "buffett_chk": buffett_chk, "model_results": results,
        "agg": agg, "decision": decision
    }

# ── UI COMPONENTS ─────────────────────────────────────────────────────────────
def card(title: str, value: str, status: str, detail: str = ""):
    """Renders a Buffett Grid card."""
    st.markdown(f"""
    <div class="buffett-card">
        <div class="card-title">{title}</div>
        <div class="card-value">{value}</div>
        <span class="card-status status-{status}">{status}</span>
        <div style="font-size: 10px; color: #888; margin-top: 8px;">{detail}</div>
    </div>
    """, unsafe_allow_html=True)

def section(title: str, icon: str = ""):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)

# ── MAIN UI ───────────────────────────────────────────────────────────────────
def main():
    st.markdown('<div class="report-title">🧐 Warren Buffett Research Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="report-subtitle">Institutional Intrinsic Value & Quality Audit</div>', unsafe_allow_html=True)

    # ── Sidebar Macro Controls ─────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Macro Assumptions")
        live_y = fetch_gsec_yield()
        gsec = st.slider("India 10Y G-Sec Yield (%)", 5.0, 10.0, live_y*100, 0.1)
        erp  = st.slider("Equity Risk Premium (%)", 3.0, 8.0, 5.0, 0.5)
        
        # Patch config
        cfg.GSEC_10Y_YIELD = gsec / 100
        cfg.EQUITY_RISK_PREMIUM = erp / 100
        
        st.divider()
        st.caption("Developed by AI Analyst | valutionStock Project")

    # ── Search Input ───────────────────────────────────────────────────────
    symbol = st.text_input("Enter NSE Ticker", placeholder="e.g. INFY, ASIANPAINT, HDFCBANK").upper().strip()
    
    if symbol:
        with st.spinner(f"Running Institutional Audit for {symbol}..."):
            report = get_full_report(symbol)
            
        if not report:
            st.error(f"Could not fetch or validate data for {symbol}. Ensure it is a valid NSE ticker.")
            return

        # Unpack
        data      = report["data"]
        dec       = report["decision"]
        agg       = report["agg"]
        bchk      = report["buffett_chk"]
        models    = report["model_results"]
        cmp       = data.get("cmp", 0)
        iv        = agg.get("weighted_iv", 0)
        disc      = dec.get("discount_pct", 0)
        verdict   = dec.get("verdict")
        
        # ── HERO ROW ───────────────────────────────────────────────────────
        st.divider()
        hcol1, hcol2, hcol3 = st.columns([2, 1, 1])
        
        with hcol1:
            st.header(f"{data.get('name')} ({symbol}.NS)")
            st.markdown(f"**Sector:** {data.get('sector')} | **Industry:** {data.get('industry')}")
            st.caption(f"Stock Type: {report['detection'].get('stock_type')} | Confidence: {agg.get('confidence')}")
        
        with hcol2:
            st.metric("Current Price", f"₹{cmp:,.2f}")
            st.metric("Weighted Fair Value", f"₹{iv:,.0f}", delta=f"{disc:+.1f}%")
            
        with hcol3:
            v_cls = verdict.replace(" ", "-") if verdict else "HOLD"
            st.markdown(f'<div class="verdict-hero hero-{v_cls}">{verdict}</div>', unsafe_allow_html=True)
            st.caption(f"Action: {dec.get('action')}")

        # ── TABS ───────────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Executive Summary", 
            "🧐 Buffett Deep Dive", 
            "📐 Valuation Math", 
            "🏢 Peer Comparison"
        ])

        # ── TAB 1: EXECUTIVE SUMMARY ───────────────────────────────────────
        with tab1:
            col_t1, col_t2 = st.columns([3, 2])
            with col_t1:
                section("Intrinsic Value Breakdown", "📐")
                # Bar chart of models
                model_plot = []
                for m_name, m_res in models.items():
                    if m_res.get("valid") and m_res.get("iv") and m_name != "Relative":
                        model_plot.append({"Model": m_name, "IV": m_res["iv"]})
                
                if model_plot:
                    df_p = pd.DataFrame(model_plot).sort_values("IV", ascending=False)
                    fig = px.bar(df_p, x="IV", y="Model", orientation='h', 
                                 text_auto=',.0f', color='IV',
                                 color_continuous_scale='RdYlGn')
                    fig.add_vline(x=cmp, line_dash="dash", line_color="blue", annotation_text=f"CMP: ₹{cmp:,.0f}")
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

            with col_t2:
                section("5-Year Financial Trend", "📈")
                rev = data.get("revenue_5y") or []
                prof = data.get("net_profit_5y") or []
                if len(rev) > 1:
                    df_trend = pd.DataFrame({
                        "Year": [f"Y-{i}" for i in range(len(rev))][::-1],
                        "Revenue": [r/1e7 for r in rev][::-1],
                        "Net Profit": [p/1e7 for p in prof][::-1]
                    })
                    st.line_chart(df_trend.set_index("Year"))
                    st.caption("Values in ₹ Crores")

            section("Investment Thesis & Flags", "💡")
            cols = st.columns(2)
            with cols[0]:
                st.subheader("✅ Positive Signals")
                for s in bchk.get("signals_found", []): st.write(f"• {s}")
            with cols[1]:
                st.subheader("🚩 Risk Flags")
                for f in dec.get("flags", []): st.write(f"• {f}")
                for r in bchk.get("red_flags", []): st.write(f"• {r}")

        # ── TAB 2: BUFFETT DEEP dive ───────────────────────────────────────
        with tab2:
            section("Warren Buffett 9-Point Quality Grid", "💎")
            
            # Gauge Score
            score = bchk.get("buffett_score", 0)
            grade = bchk.get("buffett_grade", "D")
            fig_score = go.Figure(go.Indicator(
                mode = "gauge+number", value = score,
                title = {'text': f"Buffett Score: {grade}", 'font': {'size': 24}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1F3864"},
                    'steps' : [
                        {'range': [0, 50], 'color': "#FFC7CE"},
                        {'range': [50, 75], 'color': "#FFEB9C"},
                        {'range': [75, 100], 'color': "#C6EFCE"}]
                }
            ))
            fig_score.update_layout(height=250, margin=dict(t=50, b=0))
            st.plotly_chart(fig_score, use_container_width=True)

            # The 3x3 Grid
            cl = bchk.get("checklist", {})
            g1, g2, g3 = st.columns(3)
            
            with g1:
                # 1. Moat
                m = cl.get("pricing_power", {})
                card("1. Pricing Power (Moat)", m.get("value", "N/A"), m.get("result", "NA"), "Gross Margin > 40%")
                
                # 4. Retention
                rc = cl.get("retention_check", {})
                card("4. Retention (MVA/Retained)", rc.get("value", "N/A"), rc.get("result", "NA"), "₹1 Retained >= ₹1 Mkt Val")
                
                # 7. Asset Intensity
                al = cl.get("asset_light", {})
                card("7. Asset Intensity", al.get("value", "N/A"), al.get("result", "NA"), "Capex/Revenue < 5%")

            with g2:
                # 2. Consistency
                roe = cl.get("consistent_roe", {})
                card("2. ROE Consistency", roe.get("value", "N/A"), roe.get("result", "NA"), "ROE > 15% consistently")
                
                # 5. Bond Gate
                ey = models.get("Buffett", {}).get("earnings_yield", 0)
                by = models.get("Buffett", {}).get("gsec_yield", 7)
                bg_res = "PASS" if ey > by else "FAIL"
                card("5. Bond Gate", f"{ey:.1f}% vs {by:.1f}%", bg_res, "Stock Yield > Bond Yield")
                
                # 8. Management
                mgt = "PASS" if (data.get("promoter_holding") or 0) > 0.5 and (data.get("promoter_pledge") or 0) < 0.05 else "MARGINAL"
                card("8. Management / Promoter", f"{data.get('promoter_holding',0)*100:.0f}% Held", mgt, "High holding, Low pledge")

            with g3:
                # 3. Debt Safety
                de = cl.get("debt_equity", {})
                card("3. Debt Safety", de.get("value", "N/A"), de.get("result", "NA"), "Debt/Equity < 0.5")
                
                # 6. Earnings Quality
                ocf = cl.get("ocf_quality", {})
                card("6. Earnings Quality", ocf.get("value", "N/A"), ocf.get("result", "NA"), "OCF > Net Profit")
                
                # 9. Growth
                gr = cl.get("growth_moat", {})
                card("9. Growth Consistency", gr.get("value", "N/A"), gr.get("result", "NA"), "Sales & EPS > 10% CAGR")

        # ── TAB 3: VALUATION MATH ──────────────────────────────────────────
        with tab3:
            col_m1, col_m2 = st.columns([1, 2])
            with col_m1:
                section("Buffett Owner Earnings Math", "💰")
                b = models.get("Buffett", {})
                if b.get("valid"):
                    st.metric("Owner Earnings (TTM)", f"₹{b.get('owner_earnings',0)/1e7:,.1f} Cr")
                    st.write(f"**Method:** {b.get('note')}")
                    st.write(f"**Applied Multiplier:** {b.get('multiplier'):.2f}x")
                    st.write("---")
                    st.write("*IV = Owner Earnings / (Discount Rate - Growth)*")
                else:
                    st.warning(b.get("note"))

            with col_m2:
                section("All Valuation Model Results", "🧮")
                table_data = []
                for m_name, m_res in models.items():
                    if m_name == "Relative": continue
                    table_data.append({
                        "Model": m_name,
                        "Intrinsic Value": f"₹{m_res.get('iv', 0):,.2f}" if m_res.get("valid") else "N/A",
                        "Status": "COMPUTED" if m_res.get("valid") else "SKIPPED",
                        "Note": m_res.get("note", "")[:60]
                    })
                st.table(pd.DataFrame(table_data))

            section("Margin of Safety Gauge", "🎯")
            disc_clamped = max(min(disc, 50), -50)
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta", value = disc_clamped,
                delta = {'reference': 0, 'suffix': "%"},
                gauge = {
                    'axis': {'range': [-50, 50]},
                    'bar': {'color': "#2E75B6"},
                    'steps' : [
                        {'range': [-50, 0], 'color': "#FFC7CE"},
                        {'range': [0, 15], 'color': "#FFEB9C"},
                        {'range': [15, 50], 'color': "#C6EFCE"}]
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # ── TAB 4: PEER COMPARISON ─────────────────────────────────────────
        with tab4:
            section("Relative Valuation vs Sector Medians", "🏢")
            rel = models.get("Relative", {})
            if rel.get("valid"):
                mets = rel.get("metrics", {})
                meds = rel.get("sector_medians", {})
                comp_data = []
                for k, label in [("pe", "P/E Ratio"), ("pb", "P/B Ratio"), ("ev_ebitda", "EV/EBITDA")]:
                    comp_data.append({
                        "Metric": label,
                        "This Stock": f"{mets.get(k, 0):.1f}x",
                        "Sector Median": f"{meds.get(k, 0):.1f}x",
                        "Status": rel.get("comparisons", {}).get(k, {}).get("status", "N/A")
                    })
                st.table(pd.DataFrame(comp_data))
                st.info(f"**Overall Relative Verdict:** {rel.get('overall_relative')}")
            else:
                st.write("Peer data unavailable for this sector.")

if __name__ == "__main__":
    main()
