import sys
sys.path.append('../..')

import streamlit as st
import duckdb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(
    page_title="Olist Brazil — E-Commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

@st.cache_resource
def get_con():
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "olist_ecommerce.duckdb"
    return duckdb.connect(str(db_path), read_only=True)

con = get_con()

st.title("🛒 E-Commerce Analytics — Olist Brazil")
st.caption("100,000+ real orders · 8 relational tables · 2016–2018")
st.markdown("---")

tabs = st.tabs([
    "📅 Cohort", "👥 RFM", "💰 CLV", "🔽 Funnel",
    "🛒 Basket", "📈 Growth", "⚠️ Churn",
    "📊 Pareto", "🏆 Rankings", "🚚 Logistics"
])

# ── TAB 0: COHORT ─────────────────────────────────────────────
with tabs[0]:
    st.subheader("Customer Retention Cohort Analysis")
    st.caption("When do customers come back — and when do they not?")

    cohorts = con.execute("""
        WITH first_order AS (
            SELECT c.customer_unique_id,
                   DATE_TRUNC('month',
                       MIN(o.order_purchase_timestamp::TIMESTAMP)
                   ) AS cohort_month
            FROM orders o
            JOIN customers c USING (customer_id)
            WHERE o.order_status NOT IN ('canceled','unavailable')
            GROUP BY c.customer_unique_id
        ),
        all_orders AS (
            SELECT c.customer_unique_id, f.cohort_month,
                   DATE_TRUNC('month',
                       o.order_purchase_timestamp::TIMESTAMP
                   ) AS order_month
            FROM orders o
            JOIN customers c USING (customer_id)
            JOIN first_order f USING (customer_unique_id)
        )
        SELECT cohort_month::DATE AS cohort_month,
               DATEDIFF('month', cohort_month::DATE,
                        order_month::DATE) AS period,
               COUNT(DISTINCT customer_unique_id) AS customers
        FROM all_orders
        GROUP BY cohort_month, period
        ORDER BY cohort_month, period
    """).df()

    pivot = cohorts.pivot_table(
        index="cohort_month", columns="period", values="customers"
    )
    valid = sorted([c for c in pivot.columns if 0 <= c <= 12])
    retention = pivot[valid].divide(pivot[0], axis=0) * 100

    text_vals = []
    for row in retention.values:
        text_row = []
        for val in row:
            if pd.isna(val):    text_row.append("")
            elif val >= 99.9:   text_row.append("100%")
            else:               text_row.append(f"{val:.1f}%")
        text_vals.append(text_row)

    fig = go.Figure(go.Heatmap(
        z=retention.values,
        x=[f"M+{i}" for i in valid],
        y=[str(c)[:7] for c in retention.index],
        colorscale="Blues", zmin=0, zmax=10,
        text=text_vals, texttemplate="%{text}",
        textfont={"size": 9}
    ))
    fig.update_layout(
        title="Customer Retention Cohort Heatmap — Olist Brazil",
        xaxis_title="Months since first purchase",
        yaxis_title="Acquisition cohort", height=550
    )
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg M+1 retention", "5.2%")
    c2.metric("Avg M+3 retention", "0.3%")
    c3.metric("Peak cohort", "Nov 2017 · 7,190 customers")
    st.info("**Finding:** Over 97% of customers never return after "
            "their first purchase. The Nov 2017 Black Friday spike "
            "brought the most customers but did not improve retention.")

# ── TAB 1: RFM ────────────────────────────────────────────────
with tabs[1]:
    st.subheader("RFM Customer Segmentation")
    st.caption("Recency · Frequency · Monetary")

    rfm_raw = con.execute("""
        WITH rfm AS (
            SELECT c.customer_unique_id,
                   DATEDIFF('day',
                       MAX(o.order_purchase_timestamp::DATE),
                       '2018-09-30'::DATE) AS recency,
                   COUNT(DISTINCT o.order_id) AS frequency,
                   SUM(p.payment_value)       AS monetary
            FROM orders o
            JOIN customers c USING (customer_id)
            JOIN payments p  USING (order_id)
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_unique_id
        ),
        scored AS (
            SELECT *,
                NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
                NTILE(5) OVER (ORDER BY frequency)    AS f_score,
                NTILE(5) OVER (ORDER BY monetary)     AS m_score
            FROM rfm
        ),
        segmented AS (
            SELECT *,
                CASE
                    WHEN r_score>=4 AND f_score>=4 THEN 'Champions'
                    WHEN r_score>=3 AND f_score>=3 THEN 'Loyal Customers'
                    WHEN r_score>=4 AND f_score<=2 THEN 'New Customers'
                    WHEN r_score<=2 AND f_score>=3 THEN 'At Risk'
                    WHEN r_score<=2 AND f_score>=4 THEN 'Cannot Lose Them'
                    WHEN r_score<=2 AND f_score<=2 THEN 'Hibernating'
                    ELSE 'Potential Loyalists'
                END AS segment
            FROM scored
        )
        SELECT segment,
               COUNT(*)               AS customers,
               ROUND(AVG(monetary),2) AS avg_monetary,
               ROUND(AVG(recency),0)  AS avg_recency
        FROM segmented
        GROUP BY segment
        ORDER BY customers DESC
    """).df()

    c1, c2 = st.columns(2)
    with c1:
        fig_tree = px.treemap(
            rfm_raw, path=["segment"], values="customers",
            color="avg_monetary", color_continuous_scale="Blues",
            title="Segments by Customer Count"
        )
        fig_tree.update_layout(height=400)
        st.plotly_chart(fig_tree, use_container_width=True)
    with c2:
        fig_bar = px.bar(
            rfm_raw.sort_values("customers"),
            x="customers", y="segment", orientation="h",
            color="avg_monetary", color_continuous_scale="Blues",
            title="Customers per Segment"
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.dataframe(rfm_raw, use_container_width=True)

# ── TAB 2: CLV ────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Customer Lifetime Value")
    st.caption("BG/NBD + Gamma-Gamma probabilistic models")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Repeat purchasers", "2,015", "2.2% of all")
    c2.metric("Mean CLV (12m)",    "BRL 30.86")
    c3.metric("Top CLV",           "BRL 1,400.89")
    c4.metric("VIP customers",     "17")

    tier_data = pd.DataFrame({
        "Tier":      ["Low (<20)","Medium (20-100)",
                      "High (100-500)","VIP (>500)"],
        "Customers": [1525, 366, 107, 17],
    })
    fig_clv = px.bar(
        tier_data, x="Tier", y="Customers",
        color="Tier", text="Customers",
        color_discrete_sequence=[
            "#c6dbef","#6baed6","#2171b5","#08306b"
        ],
        title="Repeat Customers by Predicted 12-Month CLV Tier"
    )
    fig_clv.update_traces(textposition="outside")
    fig_clv.update_layout(height=380, showlegend=False)
    st.plotly_chart(fig_clv, use_container_width=True)
    st.info("**Method:** BG/NBD models purchase frequency. "
            "Gamma-Gamma models average order value. "
            "Combined for 12-month per-customer CLV. "
            "Only 17 VIP customers predicted CLV > BRL 500 — "
            "these need white-glove retention treatment.")

# ── TAB 3: FUNNEL ─────────────────────────────────────────────
with tabs[3]:
    st.subheader("Order Funnel Drop-off Analysis")

    funnel_df = pd.DataFrame({
        "stage":  ["Order created","Approved","Invoiced",
                   "Processing","Shipped","Delivered"],
        "orders": [98207,98202,98200,97886,97585,96478]
    })

    c1, c2 = st.columns([2,1])
    with c1:
        fig_fun = go.Figure(go.Funnel(
            y=funnel_df["stage"], x=funnel_df["orders"],
            textinfo="value+percent initial",
            marker_color=["#08306b","#08519c","#2171b5",
                          "#4292c6","#6baed6","#c6dbef"]
        ))
        fig_fun.update_layout(height=420,
            title="Order Status Funnel")
        st.plotly_chart(fig_fun, use_container_width=True)
    with c2:
        st.markdown("### Drop-off Summary")
        st.metric("Biggest loss stage",
                  "Shipped → Delivered")
        st.metric("Orders lost at last mile", "1,107")
        st.metric("Overall delivery rate",    "97.0%")
        st.metric("Processing drop-off",      "314 orders")
        st.markdown("---")
        st.markdown("**Recommendation:** Investigate the "
                    "1,107 parcels that were shipped but "
                    "never marked delivered.")

# ── TAB 4: BASKET ─────────────────────────────────────────────
with tabs[4]:
    st.subheader("Market Basket Analysis")
    st.caption("FP-Growth — Online Retail II (UCI ML Repository)")

    rules_df = pd.DataFrame({
        "If customer buys...": [
            "Pink Blue Felt Craft Trinket Box",
            "Vintage Heads & Tails Card Game",
            "Strawberry Ceramic Trinket Box",
            "Cook With Wine Metal Sign",
            "Wooden Picture Frame White",
        ],
        "They also buy...": [
            "Pink Cream Felt Craft Trinket Box",
            "Vintage Snap Cards",
            "Sweetheart Ceramic Trinket Box",
            "Gin + Tonic Diet Metal Sign",
            "Wooden Frame Antique White",
        ],
        "Lift":       [12.49, 10.78, 10.59, 9.14, 8.93],
        "Confidence": [0.58,  0.59,  0.46,  0.48, 0.60],
        "Support":    [0.021, 0.022, 0.030, 0.022, 0.038],
    })

    fig_rules = px.scatter(
        rules_df, x="Support", y="Confidence",
        size="Lift", color="Lift",
        color_continuous_scale="Blues",
        hover_data=["If customer buys...","They also buy..."],
        title="Association Rules — Support vs Confidence"
    )
    fig_rules.update_layout(height=400)
    st.plotly_chart(fig_rules, use_container_width=True)
    st.dataframe(rules_df, use_container_width=True)
    st.info("**Lift > 1** = bought together more than by chance. "
            "Lift 12.5 = 12.5× more likely to be bought together.")

# ── TAB 5: GROWTH ─────────────────────────────────────────────
with tabs[5]:
    st.subheader("MoM / YoY Revenue Growth")

    monthly = con.execute("""
        SELECT DATE_TRUNC('month',
                   o.order_purchase_timestamp::TIMESTAMP
               )::DATE AS month,
               COUNT(DISTINCT o.order_id) AS orders,
               SUM(p.payment_value)       AS revenue,
               AVG(p.payment_value)       AS aov
        FROM orders o
        JOIN payments p USING (order_id)
        WHERE o.order_status = 'delivered'
        GROUP BY month ORDER BY month
    """).df()
    monthly["month"] = pd.to_datetime(monthly["month"])
    monthly["mom"]   = monthly["revenue"].pct_change() * 100

    c1,c2,c3 = st.columns(3)
    c1.metric("Total revenue",
              f"BRL {monthly['revenue'].sum()/1e6:.1f}M")
    c2.metric("Peak month", "Nov 2017",
              f"BRL {monthly['revenue'].max()/1e6:.1f}M")
    c3.metric("Avg order value",
              f"BRL {monthly['aov'].mean():.0f}")

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=monthly["month"], y=monthly["revenue"],
        name="Revenue", marker_color="#2171b5", opacity=0.8
    ))
    fig_rev.add_trace(go.Scatter(
        x=monthly["month"],
        y=monthly["revenue"].rolling(3).mean(),
        name="3-month avg",
        line=dict(color="orange", width=2)
    ))
    fig_rev.update_layout(
        title="Monthly Revenue with 3-Month Rolling Average",
        height=400,
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    mom_clean = monthly[monthly["month"] > "2016-12-01"].dropna(
        subset=["mom"]
    )
    colors_mom = ["#2ca02c" if v > 0 else "#d62728"
                  for v in mom_clean["mom"]]
    fig_mom = go.Figure(go.Bar(
        x=mom_clean["month"], y=mom_clean["mom"],
        marker_color=colors_mom,
        text=mom_clean["mom"].round(1).astype(str) + "%",
        textposition="outside"
    ))
    fig_mom.add_hline(y=0, line_color="gray", opacity=0.5)
    fig_mom.update_layout(
        title="Month-over-Month Revenue Growth %",
        height=380
    )
    st.plotly_chart(fig_mom, use_container_width=True)

# ── TAB 6: CHURN ──────────────────────────────────────────────
with tabs[6]:
    st.subheader("Churn Prediction Signals")
    st.caption("Gradient Boosting Classifier · ROC-AUC: 0.82")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Churn rate",     "73.8%")
    c2.metric("ROC-AUC",        "0.82")
    c3.metric("Recall churned", "96%")
    c4.metric("Features",       "12")

    imp = pd.DataFrame({
        "Feature":    [
            "Recency (days since last order)",
            "Avg review score",
            "Avg order value",
            "Avg freight paid",
            "Total orders",
            "Unique products bought",
            "Avg installments",
            "Payment types used",
            "Tenure (days as customer)",
            "Review count",
        ],
        "Importance": [0.42,0.18,0.10,0.08,0.07,
                       0.05,0.03,0.02,0.02,0.01],
    }).sort_values("Importance")

    fig_imp = px.bar(
        imp, x="Importance", y="Feature",
        orientation="h", color="Importance",
        color_continuous_scale="Blues",
        title="Feature Importance — Churn Prediction"
    )
    fig_imp.update_layout(height=440, showlegend=False)
    st.plotly_chart(fig_imp, use_container_width=True)
    st.info("**Key signal:** Recency alone explains 42% of churn. "
            "A customer who hasn't ordered in 45+ days is "
            "significantly more likely to never return.")

# ── TAB 7: PARETO ─────────────────────────────────────────────
with tabs[7]:
    st.subheader("Pareto Analysis — 80/20 Rule")

    c1,c2,c3 = st.columns(3)
    c1.metric("Products → 80% revenue",
              "Top 25.9%", "8,536 of 32,951 products")
    c2.metric("Categories → 80% revenue",
              "Top 25%", "18 of 72 categories")
    c3.metric("#1 category", "Health & Beauty",
              "BRL 1.26M revenue")

    cat_rev = con.execute("""
        SELECT COALESCE(t.product_category_name_english,
                        'Unknown') AS category,
               SUM(i.price) AS revenue
        FROM order_items i
        LEFT JOIN products p   USING (product_id)
        LEFT JOIN categories t
            ON p.product_category_name = t.product_category_name
        GROUP BY category
        ORDER BY revenue DESC
        LIMIT 20
    """).df()
    cat_rev["cum_pct"] = (
        cat_rev["revenue"].cumsum() /
        cat_rev["revenue"].sum() * 100
    )

    fig_par = make_subplots(specs=[[{"secondary_y": True}]])
    fig_par.add_trace(go.Bar(
        x=cat_rev["category"], y=cat_rev["revenue"],
        name="Revenue", marker_color="#2171b5", opacity=0.8
    ), secondary_y=False)
    fig_par.add_trace(go.Scatter(
        x=cat_rev["category"], y=cat_rev["cum_pct"],
        name="Cumulative %",
        line=dict(color="orange", width=2)
    ), secondary_y=True)
    fig_par.add_hline(y=80, line_dash="dash",
                      line_color="red",
                      annotation_text="80%",
                      secondary_y=True)
    fig_par.update_layout(
        title="Revenue Pareto — Top 20 Categories",
        xaxis_tickangle=-35, height=480,
        legend=dict(orientation="h", y=1.1)
    )
    fig_par.update_yaxes(title_text="Revenue (BRL)",
                         secondary_y=False)
    fig_par.update_yaxes(title_text="Cumulative %",
                         secondary_y=True, range=[0,105])
    st.plotly_chart(fig_par, use_container_width=True)

# ── TAB 8: RANKINGS ───────────────────────────────────────────
with tabs[8]:
    st.subheader("Seller Performance Rankings")
    st.caption(
        "Composite score: revenue 25% · review score 25% · "
        "positive reviews 20% · on-time delivery 20% · "
        "delivery speed 5% · product range 5%"
    )

    sellers = con.execute("""
        SELECT i.seller_id,
               s.seller_state,
               COUNT(DISTINCT i.order_id)     AS orders,
               ROUND(SUM(i.price), 0)         AS revenue,
               ROUND(AVG(r.review_score), 2)  AS avg_review,
               ROUND(AVG(DATEDIFF('day',
                   o.order_purchase_timestamp::DATE,
                   o.order_delivered_customer_date::DATE
               )), 1) AS avg_days,
               ROUND(COUNT(CASE WHEN
                   o.order_delivered_customer_date::DATE <=
                   o.order_estimated_delivery_date::DATE
                   THEN 1 END) * 100.0 / COUNT(*), 1) AS on_time_pct
        FROM order_items i
        JOIN sellers s USING (seller_id)
        JOIN orders o  USING (order_id)
        LEFT JOIN reviews r USING (order_id)
        WHERE o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY i.seller_id, s.seller_state
        HAVING orders >= 50
        ORDER BY revenue DESC
        LIMIT 30
    """).df()
    sellers["seller_short"] = (
        sellers["seller_id"].str[:8] + "..."
    )

    fig_sel = px.scatter(
        sellers,
        x="avg_review", y="revenue",
        size="orders", color="on_time_pct",
        color_continuous_scale="RdYlGn",
        hover_data=["seller_short","seller_state","avg_days"],
        title="Review Score vs Revenue · size=orders · "
              "colour=on-time %"
    )
    fig_sel.update_layout(height=460)
    st.plotly_chart(fig_sel, use_container_width=True)

    st.dataframe(
        sellers[["seller_short","seller_state","orders",
                 "revenue","avg_review","on_time_pct",
                 "avg_days"]].rename(
            columns={"seller_short":"Seller"}
        ),
        use_container_width=True
    )

# ── TAB 9: LOGISTICS ──────────────────────────────────────────
with tabs[9]:
    st.subheader("Delivery & Logistics KPIs")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Avg actual delivery", "12.4 days")
    c2.metric("Avg promised",        "24.4 days")
    c3.metric("Avg days early",      "12.0 days")
    c4.metric("Overall on-time",     "92.4%")

    state_kpis = con.execute("""
        SELECT c.customer_state,
               COUNT(DISTINCT o.order_id) AS deliveries,
               ROUND(AVG(DATEDIFF('day',
                   o.order_purchase_timestamp::DATE,
                   o.order_delivered_customer_date::DATE
               )), 1) AS avg_days,
               ROUND(COUNT(CASE WHEN
                   o.order_delivered_customer_date::DATE <=
                   o.order_estimated_delivery_date::DATE
                   THEN 1 END) * 100.0 / COUNT(*), 1) AS on_time_pct,
               ROUND(AVG(i.freight_value), 2) AS avg_freight,
               ROUND(AVG(r.review_score),  2) AS avg_review
        FROM orders o
        JOIN customers c   USING (customer_id)
        JOIN order_items i USING (order_id)
        LEFT JOIN reviews r USING (order_id)
        WHERE o.order_status = 'delivered'
          AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY c.customer_state
        HAVING deliveries >= 100
        ORDER BY avg_days DESC
    """).df()

    c1, c2 = st.columns(2)
    with c1:
        fig_log1 = px.bar(
            state_kpis.sort_values("avg_days"),
            x="avg_days", y="customer_state",
            orientation="h", color="avg_days",
            color_continuous_scale="RdYlGn_r",
            title="Avg Delivery Days by State"
        )
        fig_log1.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig_log1, use_container_width=True)

    with c2:
        fig_log2 = px.scatter(
            state_kpis,
            x="on_time_pct", y="avg_review",
            size="deliveries", color="avg_days",
            color_continuous_scale="RdYlGn_r",
            text="customer_state",
            title="On-time Rate vs Review Score by State"
        )
        fig_log2.update_traces(textposition="top center")
        fig_log2.update_layout(height=600)
        st.plotly_chart(fig_log2, use_container_width=True)

    st.info(
        "**Finding:** SP (São Paulo) delivers in 8.7 days. "
        "AM (Amazonas) takes 26.3 days. "
        "Late delivery directly drops review scores — "
        "the correlation is visible in the scatter plot."
    )

st.markdown("---")
st.markdown("""
**Built by Ipshita Pradhan** · PhD · Remote Sensing & Geospatial AI  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ipshita_Pradhan-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ipshita-priyadarsini-pradhan/)
[![GitHub](https://img.shields.io/badge/GitHub-IpshitaPPradhan-181717?style=flat&logo=github)](https://github.com/IpshitaPPradhan)
""")