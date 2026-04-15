# Japan E-Commerce Intelligence Hub

An end-to-end data analytics project in two parts: customer intelligence on a 
real e-commerce dataset, and Japan retail market analysis using official 
government statistics.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://japan-ecommerce-analytics.streamlit.app/)

---

## Motivation

During my research experience in Japan (Ehime University and Mitsubishi Electric Corporation) I developed a deep interest in how data science is applied to real-world business problems in the Japanese market. This project combines rigorous e-commerce 
analytics with Japan's official retail statistics, reflecting the kind of analysis I would want to contribute to at organisations working at the intersection of data science and market intelligence.

The e-commerce analysis uses the Olist dataset, the richest publicly available  transactional dataset with 100k+ real orders across 8 relational tables. 
The Japan retail component pulls directly from the e-Stat API, the official portal of Japan's Statistics Bureau, which is the data source used by researchers and analysts across Japan's public and private sectors.

---

## Project Structure

    japan-ecommerce-analytics/
    ├── notebooks/
    │   ├── 01_cohort_analysis.ipynb
    │   ├── 02_rfm_segmentation.ipynb
    │   ├── 03_clv.ipynb
    │   ├── 04_funnel_analysis.ipynb
    │   ├── 05_market_basket.ipynb
    │   ├── 06_growth_analysis.ipynb
    │   ├── 07_churn_signals.ipynb
    │   ├── 08_pareto_analysis.ipynb
    │   ├── 09_seller_product_ranking.ipynb
    │   ├── 10_logistics_kpis.ipynb
    │   └── 11_japan_retail_estat.ipynb
    ├── src/
    │   ├── data_loader.py
    │   └── estat_api.py
    ├── dashboard/
    │   ├── app.py
    │   └── pages/
    │       ├── 1_Olist_Brazil.py
    │       └── 2_Japan_Retail.py
    ├── data/
    │   └── olist_ecommerce.duckdb
    ├── docs/
    │   └── screenshots/
    ├── requirements.txt
    └── README.md

---

## Part 1 — E-Commerce Analytics (Olist Brazil)

**Dataset:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
**Scale:** 100,000+ real orders · 8 relational tables · September 2016 – August 2018

### 10 Analytics Modules

| # | Module | Technique | Key Finding |
|---|--------|-----------|-------------|
| 01 | Cohort Analysis | Retention heatmap | 97% of customers never return after first purchase |
| 02 | RFM Segmentation | Quintile scoring | 16% are Champions; 20% are Hibernating |
| 03 | Customer Lifetime Value | BG/NBD + Gamma-Gamma | Only 2.2% repeat; top CLV = BRL 1,400 |
| 04 | Funnel Drop-off | Order status conversion | 97% delivery rate; 1,107 orders lost at last mile |
| 05 | Market Basket Analysis | FP-Growth | Trinket box pairs: lift = 12.5× |
| 06 | MoM / YoY Growth | Rolling averages | Revenue grew 20× in 13 months |
| 07 | Churn Prediction | Gradient Boosting | ROC-AUC 0.82; recency explains 42% of churn |
| 08 | Pareto Analysis | Cumulative revenue | Top 26% of products = 80% of revenue |
| 09 | Seller Rankings | Composite score | São Paulo sellers dominate; small sellers score higher on reviews |
| 10 | Logistics KPIs | SLA by state | SP delivers in 8.7 days; AM takes 26.3 days |

---

## Part 2 — Japan Retail Market Intelligence (e-Stat API)

**Dataset:** [e-Stat Statistics Dashboard API](https://www.e-stat.go.jp/api/en) — Statistics Bureau of Japan  
**Scale:** 55 years of CPI data (1970–2026) · 47 prefectures · 2023–2024 retail census

### 8 Analysis Modules

| Module | Data | Key Finding |
|--------|------|-------------|
| 55-year CPI history | Monthly 1970–2026 | Japan prices rose from 30 to 112 (2020 base) |
| Rice crisis 2024–2026 | Food CPI | Rice CPI hit 213.8 — more than doubled since 2020 |
| BoJ 2% target tracking | YoY inflation | Above 2% target for 30+ consecutive months since 2022 |
| Era comparison | 7 economic eras | Deflation avg -0.28%; Post-COVID avg +2.84% |
| 6-month CPI forecast | Linear regression | Forecast: CPI ~115 by August 2026 |
| Retail by industry | 2023 + 2024 census | Nonstore (e-commerce) is fastest growing segment |
| Establishments by prefecture | 2021 census | Tokyo, Osaka, Aichi account for largest retail concentration |
| Wholesale vs retail split | Annual census | Wholesale trade = ¥457 trillion; Retail = ¥143 trillion |

---

## Design Decisions

**Why Olist (Brazil)?**  
No publicly available Japan e-commerce dataset provides the same depth — 
100k real orders across 8 linked tables covering customers, sellers, products, 
payments, reviews, and logistics. The analytical techniques demonstrated are 
geography-agnostic and directly applicable to any e-commerce platform including 
Japanese marketplaces such as Rakuten, Amazon Japan, and Yahoo Shopping.

**Why e-Stat?**  
e-Stat is the official portal for Japanese government statistics, used by 
researchers and analysts across Japan's public and private sectors. Integrating 
its API demonstrates familiarity with Japan's data infrastructure — a practical 
skill for data roles in Japan.

**Why combine them?**  
Real-world data scientists rarely work with a single source. This project 
reflects production reality: deep transactional analysis alongside official 
macro statistics for richer business context.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Language | Python 3.13 |
| Database | DuckDB |
| Data manipulation | Pandas, NumPy |
| Visualisation | Plotly |
| Dashboard | Streamlit |
| ML / Statistics | Scikit-learn, Lifetimes, MLxtend |
| Data sources | Kaggle API, UCI ML Repo, e-Stat API |
| Version control | Git + GitHub |

---

## How to Run Locally

**1. Clone the repository**

    git clone https://github.com/IpshitaPPradhan/japan-ecommerce-analytics.git
    cd japan-ecommerce-analytics

**2. Create virtual environment**

    uv venv
    venv\Scripts\activate

**3. Install dependencies**

    uv pip install -r requirements.txt

**4. Set up credentials — create a `.env` file**

    KAGGLE_USERNAME=your_username
    KAGGLE_KEY=your_key
    ESTAT_APP_ID=your_estat_id

**5. Download and load data**

    kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/
    python src/data_loader.py
    python src/estat_api.py

**6. Run dashboard**

    cd dashboard
    streamlit run app.py
---

## Data Sources

| Dataset | Source | License |
|---------|--------|---------|
| Olist Brazilian E-Commerce | [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | CC BY-NC-SA 4.0 |
| Online Retail II | [UCI ML Repository](https://archive.ics.uci.edu/dataset/502) | CC BY 4.0 |
| Japan CPI + Retail Statistics | [e-Stat API](https://www.e-stat.go.jp/api/en) | Japanese Government Statistics |

---

## About

**Ipshita Pradhan** — PhD in Remote Sensing, IIT Mandi  
Research experience: Ehime University (Japan) · Mitsubishi Electric Corporation  
Interests: Geospatial AI · Data Science · Earth Observation · Japanese market analytics

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Ipshita_Pradhan-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/ipshita-priyadarsini-pradhan/)
[![GitHub](https://img.shields.io/badge/GitHub-IpshitaPPradhan-181717?style=flat&logo=github)](https://github.com/IpshitaPPradhan)