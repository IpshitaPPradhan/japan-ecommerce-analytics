import sys
sys.path.append('../..')

import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from sklearn.linear_model import LinearRegression
from pathlib import Path

st.set_page_config(
    page_title="Japan Retail Intelligence",
    page_icon="🇯🇵",
    layout="wide"
)

@st.cache_resource
def get_con():
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "olist_ecommerce.duckdb"
    return duckdb.connect(str(db_path), read_only=True)

con = get_con()

st.title("🇯🇵 Japan Retail Market Intelligence")
st.caption(
    "Source: e-Stat Statistics Dashboard API · "
    "Statistics Bureau of Japan · Official government data"
)
st.markdown("---")

tabs = st.tabs([
    "📈 CPI History",
    "🍚 Rice Crisis",
    "🕰️ Era Comparison",
    "🔮 Forecast",
    "🏪 Retail Industry",
    "🗾 Prefectures",
])

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_cpi():
    df = con.execute("SELECT * FROM estat_cpi").df()
    df["date"] = pd.to_datetime(df["date"])
    item_map = {
        "0001":"All items","0002":"Food","0003":"Cereals",
        "0004":"Rice","0005":"Bread",
        "1001":"Rice-A","1002":"Rice-B"
    }
    df["item_name"] = df["item_code"].map(item_map)
    return df

@st.cache_data
def load_retail_ind():
    return con.execute(
        "SELECT * FROM estat_retail_industry"
    ).df()

@st.cache_data
def load_retail_pref():
    return con.execute(
        "SELECT * FROM estat_retail_pref"
    ).df()

cpi_df     = load_cpi()
retail_ind = load_retail_ind()
retail_pref = load_retail_pref()

# ── TAB 0: CPI HISTORY ────────────────────────────────────────
with tabs[0]:
    st.subheader("55 Years of Japan CPI — 1970 to 2026")

    cpi_all = cpi_df[
        cpi_df["item_name"] == "All items"
    ].sort_values("date").copy()
    cpi_all["yoy"] = cpi_all["cpi_value"].pct_change(12) * 100

    view = st.radio(
        "View:", ["CPI Level", "YoY Inflation %"],
        horizontal=True
    )

    eras = [
        ("1973-10-01","1975-06-01","#ffcccc","Oil Shock"),
        ("1979-01-01","1981-06-01","#ffe0cc","2nd Oil Shock"),
        ("1991-01-01","2000-01-01","#cce0ff","Deflation"),
        ("2008-09-01","2009-06-01","#ffe0ff","GFC"),
        ("2013-01-01","2015-12-01","#ccffcc","Abenomics"),
        ("2020-01-01","2021-06-01","#ffffcc","COVID-19"),
        ("2022-01-01","2026-02-01","#ffcccc","Post-COVID"),
    ]

    if view == "CPI Level":
        fig = go.Figure()
        for start,end,color,label in eras:
            fig.add_vrect(
                x0=start, x1=end,
                fillcolor=color, opacity=0.2,
                annotation_text=label,
                annotation_font_size=9, layer="below"
            )
        fig.add_trace(go.Scatter(
            x=cpi_all["date"], y=cpi_all["cpi_value"],
            mode="lines",
            line=dict(color="#08306b", width=1.5),
            name="CPI All items"
        ))
        fig.add_hline(y=100, line_dash="dash",
                      line_color="gray", opacity=0.5,
                      annotation_text="2020 base = 100")
        fig.update_layout(
            title="Japan CPI — 55 Years of Economic History",
            xaxis_title="Year",
            yaxis_title="CPI (2020=100)", height=500
        )
    else:
        def era_color(d):
            if d < pd.Timestamp("1976-01-01"): return "#d62728"
            elif d < pd.Timestamp("1990-01-01"): return "#aec7e8"
            elif d < pd.Timestamp("2012-01-01"): return "#1f77b4"
            elif d < pd.Timestamp("2020-01-01"): return "#2ca02c"
            elif d < pd.Timestamp("2022-01-01"): return "#ff7f0e"
            else: return "#d62728"

        colors = [era_color(d) for d in cpi_all["date"]]
        fig = go.Figure(go.Bar(
            x=cpi_all["date"], y=cpi_all["yoy"],
            marker_color=colors
        ))
        fig.add_hline(y=2, line_dash="dash",
                      line_color="red",
                      annotation_text="BoJ 2% target")
        fig.add_hline(y=0, line_color="gray", opacity=0.4)
        fig.update_layout(
            title="Japan YoY Inflation % — 1970 to 2026",
            xaxis_title="Year",
            yaxis_title="YoY %", height=500
        )

    st.plotly_chart(fig, use_container_width=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("CPI Feb 2026",     "112.2")
    c2.metric("Peak inflation",
              "1974 · +23% YoY")
    c3.metric("Deflation era",
              "1999–2012 · avg -0.28%")

# ── TAB 1: RICE CRISIS ────────────────────────────────────────
with tabs[1]:
    st.subheader("🍚 Japan Food Price Crisis — 2020 to 2026")
    st.markdown(
        "Rice prices have **more than doubled** since 2020. "
        "This is one of the most significant food price events "
        "in Japan's post-war economic history."
    )

    rice_items = ["All items","Food","Rice","Bread","Cereals"]
    rice_df = cpi_df[
        (cpi_df["item_name"].isin(rice_items)) &
        (cpi_df["date"] >= "2020-01-01")
    ].sort_values("date")

    fig_r = px.line(
        rice_df, x="date", y="cpi_value",
        color="item_name",
        title="Japan Food Price Surge — CPI by Category (2020=100)",
        labels={"cpi_value":"CPI (2020=100)",
                "date":"Month",
                "item_name":"Category"},
        color_discrete_map={
            "All items":"#636363","Food":"#fd8d3c",
            "Rice":"#d62728","Bread":"#6baed6",
            "Cereals":"#e6550d"
        }
    )
    fig_r.add_hline(y=100, line_dash="dash",
                    line_color="gray", opacity=0.5,
                    annotation_text="2020 base")
    fig_r.add_hline(y=200, line_dash="dot",
                    line_color="red", opacity=0.6,
                    annotation_text="200% — prices doubled")

    latest_rice = rice_df[
        rice_df["item_name"]=="Rice"
    ].iloc[-1]
    fig_r.add_annotation(
        x=latest_rice["date"],
        y=latest_rice["cpi_value"],
        text=f"Rice: {latest_rice['cpi_value']:.1f}",
        showarrow=True, arrowhead=2,
        font=dict(size=11, color="red"),
        bgcolor="white"
    )
    fig_r.update_layout(height=480,
        legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_r, use_container_width=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Rice CPI Feb 2026",  "213.8", "+113.8%")
    c2.metric("Cereals CPI",        "150.8", "+50.8%")
    c3.metric("Food CPI",           "129.0", "+29.0%")
    c4.metric("All items CPI",      "112.2", "+12.2%")

    st.warning(
        "🍚 **Rice crisis context:** Japan experienced severe rice shortages "
        "in 2024 partly due to poor harvests and rising export demand. "
        "The CPI data reflects this directly — rice is now 2.1× its 2020 price."
    )

# ── TAB 2: ERA COMPARISON ─────────────────────────────────────
with tabs[2]:
    st.subheader("Japan Inflation — 7 Economic Eras Compared")

    era_df = pd.DataFrame([
        ("Oil Shock",        "1973–1975", 15.54,  23.4),
        ("Bubble Economy",   "1987–1991",  1.88,   3.4),
        ("Deflation Era",    "1999–2012", -0.28,  -1.4),
        ("Abenomics",        "2013–2019",  0.82,   3.3),
        ("COVID Period",     "2020–2021", -0.13,  -1.0),
        ("Post-COVID Surge", "2022–2024",  2.84,   4.3),
        ("2025-26 Current",  "2025–2026",  2.92,   3.5),
    ], columns=["Era","Period","Avg YoY %","Peak YoY %"])

    c1, c2 = st.columns(2)
    with c1:
        fig_era = px.bar(
            era_df, x="Era", y="Avg YoY %",
            color="Avg YoY %",
            color_continuous_scale="RdYlGn_r",
            text=era_df["Avg YoY %"].astype(str)+"%",
            title="Avg Inflation by Era"
        )
        fig_era.add_hline(
            y=2, line_dash="dash", line_color="red",
            annotation_text="BoJ 2% target"
        )
        fig_era.update_traces(textposition="outside")
        fig_era.update_layout(
            height=420, xaxis_tickangle=-20,
            showlegend=False
        )
        st.plotly_chart(fig_era, use_container_width=True)

    with c2:
        st.markdown("### Era Summary")
        st.dataframe(era_df, use_container_width=True,
                     height=300)
        st.markdown("---")
        st.markdown("""
**Key observations:**
- Japan was in **deflation for 13 years** (1999–2012)
- BoJ's 2% target was **not met** during Abenomics
- Post-COVID surge is the **first sustained inflation** since 1991
- Current 2025–26 level continues **above the 2% target**
        """)

# ── TAB 3: FORECAST ───────────────────────────────────────────
with tabs[3]:
    st.subheader("🔮 CPI 6-Month Forecast — Linear Regression")
    st.caption(
        "Simple linear trend fitted on 2024 data. "
        "Indicative only — not a structural economic model."
    )

    cpi_all_modern = cpi_df[
        (cpi_df["item_name"]=="All items") &
        (cpi_df["date"] >= "2022-01-01")
    ].sort_values("date").copy()

    recent = cpi_df[
        (cpi_df["item_name"]=="All items") &
        (cpi_df["date"] >= "2024-01-01")
    ].sort_values("date").copy()
    recent["t"] = range(len(recent))

    lr = LinearRegression()
    lr.fit(recent[["t"]], recent["cpi_value"])

    future_dates = pd.date_range(
        start=recent["date"].max() +
              pd.DateOffset(months=1),
        periods=6, freq="MS"
    )
    future_t   = range(len(recent), len(recent)+6)
    future_cpi = lr.predict(
        pd.DataFrame({"t": future_t})
    )

    fig_fore = go.Figure()
    fig_fore.add_trace(go.Scatter(
        x=cpi_all_modern["date"],
        y=cpi_all_modern["cpi_value"],
        mode="lines",
        line=dict(color="#08519c", width=2),
        name="Actual CPI"
    ))
    fig_fore.add_trace(go.Scatter(
        x=future_dates, y=future_cpi,
        mode="lines+markers",
        line=dict(color="#d62728", width=2, dash="dot"),
        marker=dict(size=8),
        name="Forecast (6 months)"
    ))
    fig_fore.add_trace(go.Scatter(
        x=list(future_dates)+list(future_dates[::-1]),
        y=list(future_cpi+0.8)+list((future_cpi-0.8)[::-1]),
        fill="toself",
        fillcolor="rgba(214,39,40,0.1)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Forecast range ±0.8"
    ))
    fig_fore.add_hline(
        y=100, line_dash="dash",
        line_color="gray", opacity=0.4,
        annotation_text="2020 base"
    )
    fig_fore.update_layout(
        title="Japan CPI — Actual + 6-Month Linear Forecast",
        xaxis_title="Month",
        yaxis_title="CPI (2020=100)", height=460,
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_fore, use_container_width=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("CPI Feb 2026",
              f"{recent['cpi_value'].iloc[-1]:.1f}")
    c2.metric("Forecast Aug 2026",
              f"{future_cpi[-1]:.1f}")
    c3.metric("Monthly trend",
              f"+{lr.coef_[0]:.3f} pts/month")

    st.info(
        "**Methodology note:** Fitted on 2024 monthly data using "
        "OLS linear regression. The model captures the steady "
        "upward trend but does not account for structural breaks, "
        "policy changes, or supply shocks."
    )

# ── TAB 4: RETAIL INDUSTRY ────────────────────────────────────
with tabs[4]:
    st.subheader("Japan Retail Sales by Industry — 2023 vs 2024")

    ind_map = {
        "0207":"General Merchandise",
        "0208":"Apparel",
        "0209":"Food & Beverage",
        "0210":"Machinery & Equipment",
        "0211":"Miscellaneous Retail",
        "0212":"Nonstore (E-commerce)",
    }

    retail_cats = retail_ind[
        (retail_ind["tab"]=="0222") &
        (retail_ind["industry_code"].isin(ind_map.keys()))
    ].copy()
    retail_cats["industry_name"] = (
        retail_cats["industry_code"].map(ind_map)
    )
    retail_cats["value_bn"] = retail_cats["value"] / 1_000_000

    fig_ind = px.bar(
        retail_cats,
        x="industry_name", y="value_bn",
        color="year", barmode="group",
        color_discrete_map={2023:"#6baed6",2024:"#08519c"},
        title="Japan Retail Annual Sales 2023 vs 2024 (¥ Billions)",
        labels={"value_bn":"¥ Billions",
                "industry_name":"Category","year":"Year"}
    )
    fig_ind.update_layout(
        height=440, xaxis_tickangle=-15,
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_ind, use_container_width=True)

    pivot_ind = retail_cats.pivot_table(
        index="industry_name",
        columns="year", values="value"
    ).reset_index()
    pivot_ind.columns = ["Category","2023","2024"]
    pivot_ind["YoY Growth %"] = (
        (pivot_ind["2024"]-pivot_ind["2023"]) /
        pivot_ind["2023"] * 100
    ).round(2)

    fig_yoy = px.bar(
        pivot_ind.sort_values("YoY Growth %"),
        x="YoY Growth %", y="Category",
        orientation="h",
        color="YoY Growth %",
        color_continuous_scale="RdYlGn",
        text=pivot_ind.sort_values(
            "YoY Growth %")["YoY Growth %"].astype(str)+"%",
        title="YoY Sales Growth by Retail Category (2023→2024)"
    )
    fig_yoy.add_vline(x=0, line_color="gray", opacity=0.5)
    fig_yoy.update_traces(textposition="outside")
    fig_yoy.update_layout(height=380,
        margin=dict(l=200), showlegend=False)
    st.plotly_chart(fig_yoy, use_container_width=True)

# ── TAB 5: PREFECTURES ────────────────────────────────────────
with tabs[5]:
    st.subheader("Retail Establishments by Prefecture — Japan 2021")

    pref_names = {
        "01000":"Hokkaido","02000":"Aomori","03000":"Iwate",
        "04000":"Miyagi","05000":"Akita","06000":"Yamagata",
        "07000":"Fukushima","08000":"Ibaraki","09000":"Tochigi",
        "10000":"Gunma","11000":"Saitama","12000":"Chiba",
        "13000":"Tokyo","14000":"Kanagawa","15000":"Niigata",
        "16000":"Toyama","17000":"Ishikawa","18000":"Fukui",
        "19000":"Yamanashi","20000":"Nagano","21000":"Gifu",
        "22000":"Shizuoka","23000":"Aichi","24000":"Mie",
        "25000":"Shiga","26000":"Kyoto","27000":"Osaka",
        "28000":"Hyogo","29000":"Nara","30000":"Wakayama",
        "31000":"Tottori","32000":"Shimane","33000":"Okayama",
        "34000":"Hiroshima","35000":"Yamaguchi",
        "36000":"Tokushima","37000":"Kagawa","38000":"Ehime",
        "39000":"Kochi","40000":"Fukuoka","41000":"Saga",
        "42000":"Nagasaki","43000":"Kumamoto","44000":"Oita",
        "45000":"Miyazaki","46000":"Kagoshima","47000":"Okinawa",
    }

    ind_filter = st.selectbox(
        "Industry:",
        ["I — All Retail & Wholesale",
         "I1 — Wholesale Only",
         "I2 — Retail Only"],
        index=0
    )
    ind_code = ind_filter.split(" ")[0]

    unit_filter = st.radio(
        "Metric:", ["number of establishments","persons"],
        horizontal=True
    )

    estab = retail_pref[
        (retail_pref["area_code"].str.len()==5) &
        (retail_pref["area_code"].str.endswith("000")) &
        (retail_pref["area_code"] != "00000") &
        (retail_pref["industry_code"] == ind_code) &
        (retail_pref["unit"] == unit_filter)
    ].copy()
    estab["pref_name"] = estab["area_code"].map(pref_names)
    estab = estab[estab["pref_name"].notna()].sort_values("value")

    label = ("Establishments"
             if unit_filter=="number of establishments"
             else "Persons employed")

    fig_pref = px.bar(
        estab, x="value", y="pref_name",
        orientation="h", color="value",
        color_continuous_scale="Blues",
        title=f"Japan — {label} by Prefecture (2021)",
        labels={"value": label, "pref_name":"Prefecture"}
    )
    fig_pref.update_layout(height=900, showlegend=False,
                           margin=dict(r=60))
    st.plotly_chart(fig_pref, use_container_width=True)

    top3 = estab.nlargest(3,"value")["pref_name"].tolist()
    bot3 = estab.nsmallest(3,"value")["pref_name"].tolist()
    c1,c2 = st.columns(2)
    c1.markdown(f"**Top 3:** {', '.join(top3)}")
    c2.markdown(f"**Bottom 3:** {', '.join(bot3)}")

st.markdown("---")
st.markdown("""
**Built by Ipshita Pradhan** · PhD · Remote Sensing & Geospatial AI  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ipshita_Pradhan-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ipshita-priyadarsini-pradhan/)
[![GitHub](https://img.shields.io/badge/GitHub-IpshitaPPradhan-181717?style=flat&logo=github)](https://github.com/IpshitaPPradhan)
""")