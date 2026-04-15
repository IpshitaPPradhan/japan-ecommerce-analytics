import streamlit as st

st.set_page_config(
    page_title="E-Commerce Intelligence Hub",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ E-Commerce Intelligence Hub")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("## 🛒 Part 1 — E-Commerce Analytics")
    st.markdown("**Dataset:** Olist Brazilian E-Commerce")
    st.markdown("**Scale:** 100,000+ real orders · 8 linked tables · 2016–2018")
    st.markdown("""
**10 Analytics Modules:**
- 📅 Cohort Analysis
- 👥 RFM Segmentation
- 💰 Customer Lifetime Value
- 🔽 Funnel Drop-off
- 🛒 Market Basket Analysis
- 📈 MoM / YoY Growth
- ⚠️ Churn Prediction
- 📊 Pareto Analysis
- 🏆 Seller Rankings
- 🚚 Logistics KPIs
    """)

with col2:
    st.markdown("## 🇯🇵 Part 2 — Japan Retail Intelligence")
    st.markdown("**Dataset:** e-Stat Official Statistics API")
    st.markdown("**Scale:** 55 years CPI · 47 prefectures · 2023–2024 census")
    st.markdown("""
**8 Analysis Modules:**
- 📈 55-year CPI history
- 🍚 Rice crisis 2024–2026
- 🏦 BoJ 2% target tracking
- 🕰️ Era comparison
- 🔮 6-month CPI forecast
- 🏪 Retail by industry
- 🗾 Establishments by prefecture
- ⚖️ Wholesale vs retail split
    """)

st.markdown("---")

c1, c2, c3 = st.columns(3)
c1.metric("Real orders analysed", "100,000+")
c2.metric("Years of Japan CPI",   "55 years")
c3.metric("Analytics modules",    "18 total")

st.markdown("---")
st.markdown("""
**Built by Ipshita Pradhan** · PhD · Remote Sensing & Geospatial AI · IIT Mandi  
Stack: `Python` · `DuckDB` · `Pandas` · `Plotly` · `Streamlit` · `Scikit-learn` · `Lifetimes` · `MLxtend`  

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ipshita_Pradhan-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ipshita-priyadarsini-pradhan/)
[![GitHub](https://img.shields.io/badge/GitHub-IpshitaPPradhan-181717?style=flat&logo=github)](https://github.com/IpshitaPPradhan)
""")