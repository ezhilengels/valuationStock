# =============================================================================
# dashboard.py — Streamlit Web Dashboard
# NSE Stock Valuation Bot | Phase 5
#
# Run:  streamlit run dashboard.py
# =============================================================================

import sys
import os
import time
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Union, List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "NSE Stock Valuation Bot",
    page_icon   = "📈",
    layout      = "wide",
    initial_sidebar_state = "expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stMetric { background: #f8f9fa; border-radius: 8px; padding: 12px; }
    .verdict-box {
        padding: 18px 24px; border-radius: 10px;
        text-align: center; font-size: 22px; font-weight: bold;
        margin: 10px 0;
    }
    .strong-buy { background:#00B050; color:white; }
    .buy        { background:#92D050; color:#1a1a1a; }
    .hold       { background:#FFEB9C; color:#1a1a1a; }
    .overvalued { background:#FFC7CE; color:#1a1a1a; }
    .avoid      { background:#FF4444; color:white; }
    .early      { background:#FFD700; color:#1a1a1a; }
    .section-header {
        font-size: 16px; font-weight: 600; color: #1F3864;
        border-bottom: 2px solid #2E75B6; padding-bottom: 4px;
        margin: 18px 0 10px 0;
    }
    div[data-testid="metric-container"] {
        background: #f0f4ff; border-radius: 8px; padding: 10px 14px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/stock-share.png", width=60)
    st.title("NSE Valuation Bot")
    st.caption("India Stock Analysis | Phase 5")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Single Stock Analysis",
         "🔍 Batch Scanner",
         "📋 Watchlist Manager",
         "📖 About & Help"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("⚙️ Settings")
    gsec = st.slider("G-Sec Yield (%)", 5.0, 10.0, 7.0, 0.1,
                     help="10-year RBI G-Sec yield. Affects Graham adjusted & earnings yield.")
    wacc = st.slider("WACC Large Cap (%)", 10.0, 16.0, 12.0, 0.5,
                     help="Discount rate for DCF and EPV models.")
    mos  = st.slider("Min Margin of Safety (%)", 10, 40, 20, 5,
                     help="Minimum discount to IV required to show BUY signal.")

    # Patch config dynamically
    import config as cfg
    cfg.GSEC_10Y_YIELD       = gsec / 100
    cfg.DISCOUNT_RATE_LARGE_CAP = wacc / 100
    cfg.BUY_THRESHOLD        = mos / 100

    st.divider()
    st.caption("Data via yfinance · NSE India")


# =============================================================================
# HELPERS
# =============================================================================

@st.cache_data(ttl=1800, show_spinner=False)   # Cache 30 mins
def run_valuation(symbol: str) -> dict:
    """Run the full pipeline and cache the result."""
    from data.fetcher             import fetch_stock_data
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

    raw = fetch_stock_data(symbol)
    if not raw:
        return None
    data = clean(raw)
    is_valid, warnings = validate(data)
    if not is_valid:
        return None

    detection = detect(data)
    models    = detection.get("models_to_use", [])
    is_pharma = "pharma" in (data.get("sector") or "").lower()
    quality   = quality_run(data)

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

    agg      = aggregate(model_results, detection)
    relative = model_results.get("Relative")
    decision = decide(data.get("cmp"), agg, quality, relative, detection)

    return {
        "symbol"        : symbol,
        "name"          : data.get("name"),
        "cmp"           : data.get("cmp"),
        "iv"            : agg.get("weighted_iv"),
        "discount"      : decision.get("discount_pct"),
        "verdict"       : decision.get("verdict"),
        "quality"       : quality.get("grade"),
        "data"          : data,
        "detection"     : detection,
        "quality_result": quality,
        "model_results" : model_results,
        "agg"           : agg,
        "decision"      : decision,
    }


def verdict_badge(verdict: str):
    cls_map = {
        "STRONG BUY"              : "strong-buy",
        "BUY"                     : "buy",
        "HOLD"                    : "hold",
        "OVERVALUED"              : "overvalued",
        "AVOID"                   : "avoid",
        "EARLY STAGE — SPECULATIVE": "early",
    }
    cls = cls_map.get(verdict, "hold")
    st.markdown(f'<div class="verdict-box {cls}">{verdict}</div>',
                unsafe_allow_html=True)


def section(title: str):
    st.markdown(f'<div class="section-header">{title}</div>',
                unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)   # Cache 1 hour (P/E history rarely changes)
def fetch_pe_history(symbol: str, period: str = "5y") -> Union[pd.DataFrame, None]:
    """
    Fetch historical weekly closing prices and compute rolling P/E band.

    Returns a DataFrame with columns:
        Date, Close, PE, PE_Mean, PE_Std, PE_Upper, PE_Lower
    Returns None if EPS is unavailable or symbol not found.
    """
    try:
        import yfinance as yf
        ns_symbol = symbol if symbol.endswith(".NS") else symbol + ".NS"
        ticker    = yf.Ticker(ns_symbol)
        hist      = ticker.history(period=period, interval="1wk")

        if hist.empty:
            return None

        info = ticker.info
        eps  = info.get("trailingEps")
        if not eps or eps <= 0:
            return None

        df = hist[["Close"]].copy().reset_index()
        df.columns = ["Date", "Close"]
        df["PE"] = df["Close"] / eps

        # Rolling 52-week stats (52 weeks = 1Y window)
        roll = df["PE"].rolling(window=52, min_periods=4)
        df["PE_Mean"]  = roll.mean()
        df["PE_Std"]   = roll.std()
        df["PE_Upper"] = df["PE_Mean"] + df["PE_Std"]
        df["PE_Lower"] = (df["PE_Mean"] - df["PE_Std"]).clip(lower=0)

        # Global mean / std for band labels
        df["PE_Global_Mean"]  = df["PE"].mean()
        df["PE_Global_Upper"] = df["PE_Global_Mean"] + df["PE"].std()
        df["PE_Global_Lower"] = max(0, df["PE_Global_Mean"] - df["PE"].std())

        return df
    except Exception:
        return None


# =============================================================================
# PAGE 1 — SINGLE STOCK ANALYSIS
# =============================================================================

if page == "📊 Single Stock Analysis":

    st.title("📊 Single Stock Valuation")
    st.caption("Enter any NSE ticker to run all valuation models instantly.")

    # ── Input ──────────────────────────────────────────────────────────────
    col_inp, col_btn, col_eg = st.columns([3, 1, 4])
    with col_inp:
        symbol_input = st.text_input(
            "NSE Ticker Symbol",
            placeholder="e.g. INFY, HDFCBANK, COALINDIA",
            label_visibility="collapsed"
        ).upper().strip()
    with col_btn:
        analyse_btn = st.button("Analyse ▶", type="primary", use_container_width=True)
    with col_eg:
        st.caption("Try: INFY · HDFCBANK · COALINDIA · RELIANCE · ASIANPAINT · TATASTEEL")

    if analyse_btn and symbol_input:
        with st.spinner(f"Fetching live NSE data for {symbol_input}..."):
            result = run_valuation(symbol_input)

        if not result:
            st.error(f"Could not fetch data for **{symbol_input}**. "
                     "Check the ticker spelling (use NSE symbol, e.g. HDFCBANK not HDFC-BANK).")
            st.stop()

        data         = result["data"]
        detection    = result["detection"]
        quality      = result["quality_result"]
        model_results= result["model_results"]
        agg          = result["agg"]
        decision     = result["decision"]
        cmp          = result["cmp"]
        iv           = result["iv"]
        disc         = result["discount"]
        verdict      = result["verdict"]
        name         = result["name"]
        sector       = data.get("sector", "N/A")
        stock_type   = detection.get("stock_type", "N/A")

        # ── Top Bar ─────────────────────────────────────────────────────────
        st.divider()
        hcol1, hcol2 = st.columns([5, 2])
        with hcol1:
            st.subheader(f"{name}  ({symbol_input}.NS)")
            st.caption(f"Sector: **{sector}**  ·  Type: **{stock_type}**  ·  "
                       f"Confidence: **{agg.get('confidence', 'N/A')}**")
            if detection.get("warning"):
                st.warning(detection["warning"])
        with hcol2:
            verdict_badge(verdict)
            st.caption(decision.get("action", ""))

        # ── Key Metrics Row ──────────────────────────────────────────────────
        st.divider()
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        mktcap = data.get("market_cap")
        roe_list = [r for r in (data.get("roe_5y") or []) if r is not None]
        avg_roe  = sum(roe_list) / len(roe_list) if roe_list else None
        de       = data.get("debt_equity")
        rev_g    = data.get("revenue_growth_5y")

        m1.metric("CMP",        f"₹{cmp:,.2f}" if cmp else "N/A")
        m2.metric("Weighted IV", f"₹{iv:,.0f}" if iv else "N/A",
                  delta=f"{disc:+.1f}% MOS" if disc is not None else None)
        m3.metric("P/E",        f"{data.get('pe_ratio', 0):.1f}x" if data.get('pe_ratio') else "N/A")
        m4.metric("Avg ROE",    f"{avg_roe*100:.1f}%" if avg_roe else "N/A")
        m5.metric("D/E Ratio",  f"{de:.2f}" if de is not None else "N/A")
        m6.metric("Rev CAGR",   f"{rev_g*100:.1f}%" if rev_g else "N/A")

        st.divider()

        # ── Left / Right columns ─────────────────────────────────────────────
        left, right = st.columns([3, 2])

        with left:
            # IV COMPARISON CHART
            section("📐 Intrinsic Value vs CMP — All Models")

            model_names, model_ivs, model_colors = [], [], []
            MODEL_DISPLAY = {
                "Graham"       : "Graham",
                "DCF"          : "DCF",
                "Lynch"        : "Lynch",
                "Buffett"      : "Owner Earnings",
                "EPV"          : "EPV",
                "DDM"          : "DDM",
                "ExcessReturns": "Excess Returns",
                "EV/Sales"     : "EV / Sales",
                "MidCycleEV"   : "Mid-Cycle EV",
                "NAV"          : "NAV (REIT)",
                "PriceTAM"     : "Price / TAM",
            }
            for mk, display in MODEL_DISPLAY.items():
                mr = model_results.get(mk)
                if mr and mr.get("valid") and mr.get("iv"):
                    model_names.append(display)
                    model_ivs.append(mr["iv"])
                    model_colors.append(
                        "#00B050" if mr["iv"] > (cmp or 0) else "#FF4444"
                    )

            if model_names:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=model_ivs, y=model_names,
                    orientation="h",
                    marker_color=model_colors,
                    text=[f"₹{v:,.0f}" for v in model_ivs],
                    textposition="outside",
                    name="Intrinsic Value"
                ))
                if cmp:
                    fig.add_vline(
                        x=cmp, line_dash="dash", line_color="#2E75B6",
                        line_width=2,
                        annotation_text=f"CMP ₹{cmp:,.0f}",
                        annotation_position="top right"
                    )
                if iv:
                    fig.add_vline(
                        x=iv, line_dash="dot", line_color="#FF6600",
                        line_width=2,
                        annotation_text=f"Wtd IV ₹{iv:,.0f}",
                        annotation_position="bottom right"
                    )
                fig.update_layout(
                    height=max(280, len(model_names) * 45 + 80),
                    margin=dict(l=10, r=80, t=20, b=20),
                    xaxis_title="Price (₹)",
                    plot_bgcolor="#fafafa",
                    paper_bgcolor="#fafafa",
                    font=dict(size=12),
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── 5-YEAR FINANCIAL TRENDS ────────────────────────────────────
            section("📈 5-Year Financial Trends (Sales & Net Profit)")
            rev_5y = data.get("revenue_5y") or []
            np_5y  = data.get("net_profit_5y") or []
            
            # Clean and reverse (show oldest to newest)
            rev_5y = [r/1e7 for r in rev_5y if r is not None][::-1]
            np_5y  = [n/1e7 for n in np_5y if n is not None][::-1]
            years  = [f"Y-{len(rev_5y)-i-1}" for i in range(len(rev_5y))]
            if len(years) > 1:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=years, y=rev_5y, name="Sales (Cr)",
                    line=dict(color="#1F3864", width=3),
                    marker=dict(size=8)
                ))
                fig_trend.add_trace(go.Scatter(
                    x=years, y=np_5y, name="Net Profit (Cr)",
                    line=dict(color="#00B050", width=3),
                    marker=dict(size=8),
                    yaxis="y2"
                ))
                fig_trend.update_layout(
                    height=300, margin=dict(l=10, r=10, t=30, b=20),
                    plot_bgcolor="#fafafa", paper_bgcolor="#fafafa",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title="Sales (₹ Cr)", side="left"),
                    yaxis2=dict(title="Profit (₹ Cr)", side="right", overlaying="y", showgrid=False)
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Insufficient historical data for trend chart")

            # RELATIVE VALUATION TABLE
            section("📊 Relative Valuation vs Sector Peers")
            rel = (model_results.get("Relative") or {})
            metrics   = rel.get("metrics", {})
            benchmarks= rel.get("sector_medians", {})
            comps     = rel.get("comparisons", {})
            overall   = rel.get("overall_relative", "N/A")

            rel_data = []
            for key, label in [("pe","P/E"), ("pb","P/B"),
                                ("ev_ebitda","EV/EBITDA"), ("peg","PEG")]:
                sv  = metrics.get(key)
                bv  = benchmarks.get(key)
                st_ = comps.get(key, {}).get("status", "—")
                rel_data.append({
                    "Metric"        : label,
                    "Stock"         : f"{sv:.1f}x" if sv else "N/A",
                    "Sector Median" : f"{bv:.1f}x" if bv else "N/A",
                    "Status"        : st_
                })

            rel_df = pd.DataFrame(rel_data)
            def color_status(val):
                if val == "CHEAP":    return "background-color:#C6EFCE"
                if val == "EXPENSIVE":return "background-color:#FFC7CE"
                return ""
            st.dataframe(
                rel_df.style.applymap(color_status, subset=["Status"]),
                use_container_width=True, hide_index=True
            )
            ov_color = ("green" if "CHEAP" in overall
                        else "red" if "EXPENSIVE" in overall else "grey")
            st.markdown(f"**Overall vs Peers:** :{ov_color}[{overall}]")

        with right:
            # MARGIN OF SAFETY GAUGE
            section("🎯 Margin of Safety")
            if disc is not None and iv:
                disc_clamped = max(min(disc, 50), -50)
                fig_gauge = go.Figure(go.Indicator(
                    mode  = "gauge+number+delta",
                    value = disc_clamped,
                    delta = {"reference": 0, "suffix": "%"},
                    number= {"suffix": "%", "font": {"size": 32}},
                    title = {"text": "Discount to IV", "font": {"size": 14}},
                    gauge = {
                        "axis": {"range": [-50, 50],
                                 "tickvals": [-50,-30,-15,0,15,30,50]},
                        "bar" : {"color": (
                            "#00B050" if disc >= 30 else
                            "#92D050" if disc >= 15 else
                            "#FFEB9C" if disc >= 0  else
                            "#FFC7CE" if disc >= -20 else "#FF4444"
                        )},
                        "steps": [
                            {"range": [-50,-20], "color": "#FFE0E0"},
                            {"range": [-20,  0], "color": "#FFF3CD"},
                            {"range": [  0, 15], "color": "#F0FFF0"},
                            {"range": [ 15, 30], "color": "#CCFFCC"},
                            {"range": [ 30, 50], "color": "#99EE99"},
                        ],
                        "threshold": {
                            "line": {"color": "#2E75B6", "width": 3},
                            "thickness": 0.75, "value": 20
                        }
                    }
                ))
                fig_gauge.update_layout(
                    height=240, margin=dict(l=20, r=20, t=30, b=10),
                    paper_bgcolor="#fafafa"
                )
                st.plotly_chart(fig_gauge, use_container_width=True)
                st.caption(f"Blue line = {mos}% minimum margin of safety (adjustable in sidebar)")

            # QUALITY SCORECARD
            section("✅ Quality Scorecard")
            q_score = quality.get("score", 0)
            q_grade = quality.get("grade", "N/A")
            checks  = quality.get("checks", {})

            # Radial/donut score
            fig_q = go.Figure(go.Indicator(
                mode = "gauge+number",
                value= q_score,
                title= {"text": f"Quality Score — {q_grade}", "font": {"size": 13}},
                gauge= {
                    "axis" : {"range": [0, 100]},
                    "bar"  : {"color": (
                        "#00B050" if q_score >= 80 else
                        "#92D050" if q_score >= 60 else
                        "#FFEB9C" if q_score >= 40 else "#FF4444"
                    )},
                    "steps": [
                        {"range": [0,  40], "color": "#FFE0E0"},
                        {"range": [40, 60], "color": "#FFF3CD"},
                        {"range": [60, 80], "color": "#CCFFCC"},
                        {"range": [80,100], "color": "#99EE99"},
                    ]
                }
            ))
            fig_q.update_layout(
                height=200, margin=dict(l=20, r=20, t=40, b=10),
                paper_bgcolor="#fafafa"
            )
            st.plotly_chart(fig_q, use_container_width=True)

            # Pass / Fail checklist
            passed = quality.get("passed", [])
            failed = quality.get("failed", [])
            for p in passed:
                st.markdown(f"✅ {p}")
            for f in failed:
                st.markdown(f"❌ **{f}**")
            if quality.get("moat_flags"):
                st.caption("**Moat signals:** " + " · ".join(quality["moat_flags"]))

            # BUFFETT EARNINGS YIELD
            buff = model_results.get("Buffett")
            if buff and buff.get("valid") and buff.get("earnings_yield"):
                section("⚡ Buffett Earnings Yield Check")
                ey   = buff["earnings_yield"]
                gsec_y = buff["gsec_yield"]
                fig_ey = go.Figure()
                fig_ey.add_trace(go.Bar(
                    x=["Earnings Yield", "G-Sec Yield"],
                    y=[ey, gsec_y],
                    marker_color=["#00B050" if ey >= gsec_y else "#FF4444", "#2E75B6"],
                    text=[f"{ey:.2f}%", f"{gsec_y:.1f}%"],
                    textposition="outside"
                ))
                fig_ey.update_layout(
                    height=200, margin=dict(l=10, r=10, t=10, b=20),
                    plot_bgcolor="#fafafa", paper_bgcolor="#fafafa",
                    showlegend=False, yaxis_title="%"
                )
                st.plotly_chart(fig_ey, use_container_width=True)
                st.caption(buff.get("yield_verdict", ""))

        # ── Model Detail Expander ─────────────────────────────────────────────
        st.divider()
        with st.expander("🔍 Full Model Details — All Inputs & Outputs"):
            tabs = st.tabs([m for m in MODEL_DISPLAY.values()
                            if model_results.get(
                                [k for k,v in MODEL_DISPLAY.items() if v==m][0]
                            )])
            tab_models = [(k, v) for k, v in MODEL_DISPLAY.items()
                          if model_results.get(k)]
            for tab, (mk, display) in zip(tabs, tab_models):
                with tab:
                    mr = model_results[mk]
                    if not mr or not mr.get("valid"):
                        st.warning(f"Model skipped: {mr.get('note', 'N/A') if mr else 'No data'}")
                        continue
                    c1, c2 = st.columns(2)
                    with c1:
                        if mr.get("iv"):
                            st.metric("Intrinsic Value", f"₹{mr['iv']:,.0f}")
                        st.caption(f"**Note:** {mr.get('note', '—')}")
                    with c2:
                        inputs = mr.get("inputs_used", {})
                        if inputs:
                            df_in = pd.DataFrame(
                                list(inputs.items()),
                                columns=["Input", "Value"]
                            )
                            st.dataframe(df_in, hide_index=True,
                                         use_container_width=True)

        # ── Historical P/E Trend Chart ────────────────────────────────────────
        st.divider()
        section("📈 Historical P/E Band Chart")
        pe_period = st.radio(
            "Period", ["1y", "3y", "5y"], index=2,
            horizontal=True, key="pe_period_radio"
        )
        with st.spinner("Loading P/E history..."):
            pe_df = fetch_pe_history(symbol_input, pe_period)

        if pe_df is not None and not pe_df.empty:
            current_pe = data.get("pe_ratio")
            global_mean   = pe_df["PE_Global_Mean"].iloc[-1]
            global_upper  = pe_df["PE_Global_Upper"].iloc[-1]
            global_lower  = pe_df["PE_Global_Lower"].iloc[-1]

            # Build figure
            fig_pe = go.Figure()

            # ±1 Std Dev band (shaded area)
            fig_pe.add_trace(go.Scatter(
                x=list(pe_df["Date"]) + list(pe_df["Date"][::-1]),
                y=list(pe_df["PE_Upper"].fillna(method="bfill")) +
                  list(pe_df["PE_Lower"].fillna(method="bfill")[::-1]),
                fill="toself",
                fillcolor="rgba(46,117,182,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name="±1 Std Dev Band",
                showlegend=True,
                hoverinfo="skip"
            ))

            # Rolling mean P/E line
            fig_pe.add_trace(go.Scatter(
                x=pe_df["Date"], y=pe_df["PE_Mean"],
                mode="lines",
                line=dict(color="#2E75B6", dash="dash", width=1.5),
                name="Rolling Mean P/E"
            ))

            # Actual P/E line
            fig_pe.add_trace(go.Scatter(
                x=pe_df["Date"], y=pe_df["PE"],
                mode="lines",
                line=dict(color="#1F3864", width=2),
                name="P/E Ratio",
                hovertemplate="<b>%{x|%d %b %Y}</b><br>P/E: %{y:.1f}x<extra></extra>"
            ))

            # Global mean horizontal line
            fig_pe.add_hline(
                y=global_mean, line_dash="dot",
                line_color="#FF6600", line_width=1.5,
                annotation_text=f"Avg {global_mean:.1f}x",
                annotation_position="right",
                annotation_font=dict(color="#FF6600", size=11)
            )

            # Current P/E marker
            if current_pe and not pe_df.empty:
                fig_pe.add_trace(go.Scatter(
                    x=[pe_df["Date"].iloc[-1]],
                    y=[current_pe],
                    mode="markers+text",
                    marker=dict(
                        color=(
                            "#00B050" if current_pe <= global_lower
                            else "#FF4444" if current_pe >= global_upper
                            else "#FFEB9C"
                        ),
                        size=12, symbol="diamond",
                        line=dict(color="#1F3864", width=2)
                    ),
                    text=[f"Now: {current_pe:.1f}x"],
                    textposition="top center",
                    name="Current P/E",
                    showlegend=True
                ))

            # Layout
            pe_pct = "CHEAP" if current_pe and current_pe <= global_lower else \
                     "EXPENSIVE" if current_pe and current_pe >= global_upper else "FAIR"
            pe_color = "green" if pe_pct == "CHEAP" else \
                       "red" if pe_pct == "EXPENSIVE" else "orange"

            fig_pe.update_layout(
                height=340,
                margin=dict(l=10, r=80, t=20, b=40),
                xaxis_title="Date",
                yaxis_title="P/E Ratio",
                plot_bgcolor="#fafafa",
                paper_bgcolor="#fafafa",
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1),
                hovermode="x unified",
                font=dict(size=12)
            )
            st.plotly_chart(fig_pe, use_container_width=True)

            # Caption with context
            cap_parts = []
            if current_pe:
                cap_parts.append(
                    f"Current P/E **{current_pe:.1f}x** vs "
                    f"{pe_period} avg **{global_mean:.1f}x**"
                )
                cap_parts.append(
                    f"Band: **{global_lower:.1f}x – {global_upper:.1f}x**"
                )
                cap_parts.append(f"Valuation: :{pe_color}[**{pe_pct}**]")
            st.caption("  ·  ".join(cap_parts) if cap_parts else
                       "P/E history based on trailing EPS from yfinance.")

        else:
            st.info("Historical P/E chart not available — "
                    "EPS data required (profitable companies only).")

        # ── Flags Section ─────────────────────────────────────────────────────
        flags = decision.get("flags", [])
        if flags:
            with st.expander("⚠️ Flags & Warnings"):
                for flag in flags:
                    st.markdown(f"- {flag}")

        # ── Raw Financial Data ────────────────────────────────────────────────
        with st.expander("📂 Raw Financial Data"):
            raw_items = {
                "EPS (TTM)"        : data.get("eps_ttm"),
                "Book Value/Share" : data.get("book_value_per_share"),
                "DPS"              : data.get("dps"),
                "EPS Growth (5Y)"  : f"{data.get('eps_growth_5y',0)*100:.1f}%",
                "Rev Growth (5Y)"  : f"{data.get('revenue_growth_5y',0)*100:.1f}%",
                "EBIT (TTM Cr)"    : f"{(data.get('ebit_ttm') or 0)/1e7:.0f}",
                "EBITDA (TTM Cr)"  : f"{(data.get('ebitda_ttm') or 0)/1e7:.0f}",
                "Total Debt (Cr)"  : f"{(data.get('total_debt') or 0)/1e7:.0f}",
                "Cash (Cr)"        : f"{(data.get('cash') or 0)/1e7:.0f}",
                "Tax Rate"         : f"{data.get('tax_rate',0)*100:.1f}%",
                "Beta"             : data.get("beta"),
                "Is PSU"           : data.get("is_psu"),
            }
            df_raw = pd.DataFrame(
                list(raw_items.items()), columns=["Field", "Value"]
            )
            st.dataframe(df_raw, hide_index=True, use_container_width=True)


# =============================================================================
# PAGE 2 — BATCH SCANNER
# =============================================================================

elif page == "🔍 Batch Scanner":

    st.title("🔍 Batch Stock Scanner")
    st.caption("Scan an entire watchlist, filter by verdict, and export to Excel.")

    from screening.watchlists import WATCHLISTS, list_watchlists

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        wl_name = st.selectbox(
            "Select Watchlist",
            list(WATCHLISTS.keys()),
            format_func=lambda x: f"{x.replace('_',' ').title()}  ({len(WATCHLISTS[x])} stocks)"
        )
    with col2:
        filter_opt = st.selectbox(
            "Filter Results",
            ["All", "BUY only", "Undervalued (any discount)", "HOLD", "Avoid"]
        )
    with col3:
        delay = st.slider("API delay (sec)", 0.5, 3.0, 1.5, 0.5,
                          help="Seconds between API calls to avoid rate limits")

    tickers_preview = WATCHLISTS.get(wl_name, [])
    st.caption(f"Stocks in watchlist: **{', '.join(tickers_preview[:10])}**"
               + (f" ... +{len(tickers_preview)-10} more" if len(tickers_preview) > 10 else ""))

    run_scan_btn = st.button(f"🚀 Start Scan — {len(tickers_preview)} stocks",
                             type="primary")

    if run_scan_btn:
        FILTER_MAP = {
            "All"                   : None,
            "BUY only"              : "buy",
            "Undervalued (any discount)": "undervalued",
            "HOLD"                  : "hold",
            "Avoid"                 : "avoid"
        }
        filter_key = FILTER_MAP[filter_opt]

        results    = []
        failed_tickers = []
        progress   = st.progress(0, text="Initialising scanner...")
        status_box = st.empty()
        total      = len(tickers_preview)

        for i, ticker in enumerate(tickers_preview):
            status_box.caption(f"Scanning {ticker} ({i+1}/{total})...")
            progress.progress((i + 1) / total,
                              text=f"Scanning {ticker} ({i+1}/{total})")
            try:
                result = run_valuation(ticker)
                if result:
                    results.append(result)
            except Exception as e:
                failed_tickers.append(f"{ticker}: {str(e)}")
            time.sleep(delay)

        progress.empty()
        status_box.empty()

        if failed_tickers:
            with st.expander(f"⚠️ {len(failed_tickers)} stocks skipped due to errors"):
                for f in failed_tickers:
                    st.write(f"• {f}")

        # Filter
        if filter_key == "buy":
            show = [r for r in results if r.get("verdict") in ["STRONG BUY", "BUY"]]
        elif filter_key == "undervalued":
            show = [r for r in results if (r.get("discount") or 0) > 0]
        elif filter_key == "hold":
            show = [r for r in results if r.get("verdict") == "HOLD"]
        elif filter_key == "avoid":
            show = [r for r in results if r.get("verdict") in ["OVERVALUED","AVOID"]]
        else:
            show = results

        if not show:
            st.warning("No stocks match the filter. Try 'All' to see all results.")
        else:
            # Summary counts
            sc1, sc2, sc3, sc4, sc5 = st.columns(5)
            sc1.metric("Scanned",    len(results))
            sc2.metric("Strong Buy", sum(1 for r in results if r.get("verdict")=="STRONG BUY"),
                       delta_color="normal")
            sc3.metric("Buy",        sum(1 for r in results if r.get("verdict")=="BUY"))
            sc4.metric("Hold",       sum(1 for r in results if r.get("verdict")=="HOLD"))
            sc5.metric("Avoid",      sum(1 for r in results
                                         if r.get("verdict") in ["OVERVALUED","AVOID"]))

            # Results Table
            sorted_show = sorted(show,
                                 key=lambda x: x.get("discount") or -999,
                                 reverse=True)
            table_data = []
            for r in sorted_show:
                disc = r.get("discount")
                table_data.append({
                    "Ticker"   : r.get("symbol",""),
                    "Name"     : (r.get("name") or "")[:30],
                    "CMP (₹)"  : r.get("cmp"),
                    "IV (₹)"   : r.get("iv"),
                    "Discount %": round(disc, 1) if disc is not None else None,
                    "Quality"  : r.get("quality",""),
                    "Type"     : r.get("type",""),
                    "Verdict"  : r.get("verdict",""),
                })

            df = pd.DataFrame(table_data)

            def color_verdict(val):
                colors = {
                    "STRONG BUY": "background-color:#00B050;color:white",
                    "BUY"       : "background-color:#92D050",
                    "HOLD"      : "background-color:#FFEB9C",
                    "OVERVALUED": "background-color:#FFC7CE",
                    "AVOID"     : "background-color:#FF4444;color:white",
                }
                return colors.get(val, "")

            def color_discount(val):
                if val is None: return ""
                if val >= 30:   return "background-color:#00B050;color:white"
                if val >= 15:   return "background-color:#92D050"
                if val >= 0:    return "background-color:#FFEB9C"
                return "background-color:#FFC7CE"

            styled = (df.style
                      .applymap(color_verdict,  subset=["Verdict"])
                      .applymap(color_discount, subset=["Discount %"])
                      .format({"CMP (₹)": "₹{:,.0f}", "IV (₹)": "₹{:,.0f}",
                               "Discount %": "{:+.1f}%"},
                              na_rep="N/A"))
            st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

            # Verdict distribution pie chart
            verdict_counts = {}
            for r in results:
                v = r.get("verdict","N/A")
                verdict_counts[v] = verdict_counts.get(v, 0) + 1

            fig_pie = px.pie(
                values=list(verdict_counts.values()),
                names=list(verdict_counts.keys()),
                color=list(verdict_counts.keys()),
                color_discrete_map={
                    "STRONG BUY": "#00B050", "BUY": "#92D050",
                    "HOLD": "#FFEB9C", "OVERVALUED": "#FFC7CE",
                    "AVOID": "#FF4444",
                    "EARLY STAGE — SPECULATIVE": "#FFD700"
                },
                title="Verdict Distribution"
            )
            fig_pie.update_layout(height=320, margin=dict(t=40, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

            # Excel Export
            if st.button("📥 Export to Excel"):
                from output.export import export
                full_results = [r for r in show if r]
                path = export(full_results)
                st.success(f"✅ Excel saved: `{path}`")
                with open(path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Excel Report",
                        data=f,
                        file_name=os.path.basename(path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )


# =============================================================================
# PAGE 3 — WATCHLIST MANAGER
# =============================================================================

elif page == "📋 Watchlist Manager":

    st.title("📋 Watchlist Manager")
    st.caption("View, compare, and customise your stock watchlists.")

    from screening.watchlists import WATCHLISTS

    wl_sel = st.selectbox(
        "Select a watchlist to view",
        list(WATCHLISTS.keys()),
        format_func=lambda x: f"{x.replace('_',' ').title()}  ({len(WATCHLISTS[x])} stocks)"
    )

    tickers = WATCHLISTS[wl_sel]
    st.write(f"**{len(tickers)} stocks** in `{wl_sel}`:")

    # Display as grid
    cols = st.columns(6)
    for i, t in enumerate(tickers):
        cols[i % 6].code(t)

    st.divider()
    st.subheader("📊 Watchlist Overview")
    wl_data = []
    for name, ticks in WATCHLISTS.items():
        wl_data.append({
            "Watchlist"   : name.replace("_"," ").title(),
            "Stocks"      : len(ticks),
            "Focus"       : {
                "nifty50"      : "Large Cap · Diversified",
                "niftynext50"  : "Large-Mid Cap",
                "midcap50"     : "Mid Cap (50 stocks)",
                "midcap100"    : "Mid Cap 100 (extended)",
                "value_quality": "Quality / Buffett Style",
                "psu_dividend" : "PSU · Dividend Income",
                "banking"      : "Banks & NBFCs",
                "it_tech"      : "IT & Software",
                "pharma"       : "Pharma & Healthcare",
                "cyclicals"    : "Steel · Cement · Metals",
                "reits_invits" : "REITs & InvITs",
                "custom"       : "Your Custom List",
            }.get(name, "—")
        })
    st.dataframe(pd.DataFrame(wl_data), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("➕ Add to Custom Watchlist")
    new_ticker = st.text_input("Enter NSE ticker to add to custom list",
                               placeholder="e.g. PIDILITIND").upper().strip()
    if st.button("Add") and new_ticker:
        if new_ticker not in WATCHLISTS["custom"]:
            WATCHLISTS["custom"].append(new_ticker)
            st.success(f"✅ Added {new_ticker} to custom watchlist")
        else:
            st.info(f"{new_ticker} is already in the custom watchlist")


# =============================================================================
# PAGE 4 — ABOUT & HELP
# =============================================================================

elif page == "📖 About & Help":

    st.title("📖 About & Help")

    st.markdown("""
    ## NSE Stock Valuation Bot

    A complete Python-based stock scanner and valuation system for Indian
    markets (NSE), built using institutional-grade frameworks.

    ---
    ### Valuation Models Used

    | Model | Best For |
    |---|---|
    | **Benjamin Graham** (Simple + Adjusted) | All profitable stocks |
    | **DCF — 2-Stage** | IT, Pharma, Growth stocks |
    | **Peter Lynch PEG** | High-growth IT / Pharma |
    | **Buffett Owner Earnings** | Stable profitable businesses |
    | **Earnings Power Value (EPV)** | Conservative floor value |
    | **Dividend Discount Model** | PSUs, FMCG, dividend payers |
    | **Excess Returns Model** | Banks and NBFCs |
    | **EV / Sales** | Early-stage / loss-making |
    | **Mid-Cycle EV/EBITDA** | Cyclicals: Steel, Cement |

    ---
    ### Stock Type Auto-Detection

    The bot automatically detects what type of stock it is and applies
    the right model combination:

    - **BANK_NBFC** → Excess Returns Model + EPV
    - **PSU** → DDM + EV/EBITDA
    - **HIGH_GROWTH** → DCF + PEG
    - **LARGE_STABLE** → DCF + DDM + Graham
    - **CYCLICAL** → Mid-Cycle EV/EBITDA only
    - **EARLY_STAGE** → EV/Sales (no earnings models)
    - **GENERAL** → All base models with equal weights

    ---
    ### Verdict System

    | Verdict | Condition |
    |---|---|
    | **STRONG BUY** | CMP ≥ 30% below weighted IV |
    | **BUY** | CMP 15–30% below weighted IV |
    | **HOLD** | CMP within 15% of IV |
    | **OVERVALUED** | CMP 0–20% above IV |
    | **AVOID** | CMP > 20% above IV OR quality gate failed |

    ---
    ### Terminal Commands

    ```bash
    # Single stock
    python main.py INFY
    python main.py INFY --export

    # Batch scan
    python main.py --scan nifty50
    python main.py --scan value_quality --filter buy --export

    # Show all watchlists
    python main.py --lists
    ```

    ---
    ### Settings (Sidebar)
    - **G-Sec Yield** — Updates Graham adjusted formula + earnings yield comparison
    - **WACC** — Changes discount rate for DCF and EPV
    - **Min MOS** — Minimum margin of safety required for BUY signal

    ---
    *Data sourced via yfinance (NSE). For educational purposes only.
    Not financial advice. Always do your own research.*
    """)
