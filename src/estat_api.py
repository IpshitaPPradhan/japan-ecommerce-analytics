import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

ESTAT_BASE = "https://api.e-stat.go.jp/rest/3.0/app/json"
APP_ID = os.getenv("ESTAT_APP_ID", "")

# ── Dataset IDs ───────────────────────────────────────────────
CPI_ID            = "0003427113"   # 2020-base CPI, monthly, by item & area
RETAIL_PREF_ID    = "0004003264"   # Retail trade annual, by industry & prefecture
RETAIL_IND_23_ID  = "0004021940"   # Wholesale/retail by industry 2023
RETAIL_IND_24_ID  = "0004032883"   # Wholesale/retail by industry 2024


def _fetch(stats_id: str, limit: int = 10000, extra_params: dict = None) -> dict:
    """Base fetch — returns full raw JSON."""
    params = {
        "appId":       APP_ID,
        "lang":        "E",
        "statsDataId": stats_id,
        "limit":       str(limit),
    }
    if extra_params:
        params.update(extra_params)
    r = requests.get(f"{ESTAT_BASE}/getStatsData", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _values_to_df(raw: dict) -> pd.DataFrame:
    """Extract VALUE list from raw response into a flat DataFrame."""
    values = (raw.get("GET_STATS_DATA", {})
                 .get("STATISTICAL_DATA", {})
                 .get("DATA_INF", {})
                 .get("VALUE", []))
    if isinstance(values, dict):
        values = [values]
    return pd.DataFrame(values)


# ── 1. CPI Monthly ────────────────────────────────────────────
def get_cpi_monthly(area_code: str = "00000") -> pd.DataFrame:
    """
    Fetch 2020-base Consumer Price Index — monthly, nationwide.
    area_code '00000' = Japan total.
    Returns columns: year, month, date, item_code, cpi_value
    """
    print("Fetching CPI monthly data...")
    raw = _fetch(CPI_ID, limit=5000, extra_params={"cdArea": area_code})
    df = _values_to_df(raw)

    if df.empty:
        raise ValueError("CPI fetch returned no data.")

    # time format: '2026000303' → year=2026, month=03
    df = df.rename(columns={
        "@tab":   "tab",
        "@cat01": "item_code",
        "@area":  "area",
        "@time":  "time_raw",
        "$":      "cpi_value",
    })
    df["cpi_value"] = pd.to_numeric(df["cpi_value"], errors="coerce")

    # Parse time: format is YYYYMMdd where MM=month, dd=sub-period
    # e.g. '2026000303' → 2026, month 03
    df["year"]  = df["time_raw"].str[:4].astype(int)
    df["month"] = df["time_raw"].str[6:8].astype(int)
    df = df[df["month"].between(1, 12)]   # drop annual aggregates
    df["date"]  = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-01"
    )

    result = (df[["date", "year", "month", "item_code", "area", "cpi_value"]]
              .dropna(subset=["cpi_value"])
              .sort_values("date")
              .reset_index(drop=True))

    print(f"  CPI: {len(result):,} records | "
          f"{result['date'].min().date()} → {result['date'].max().date()}")
    return result


# ── 2. Retail Trade by Prefecture ─────────────────────────────
def get_retail_by_prefecture() -> pd.DataFrame:
    """
    Fetch annual retail trade (establishments + sales) by prefecture.
    Dataset: Census of Commerce 2021.
    Returns columns: area_code, tab, industry_code, value, unit
    """
    print("Fetching retail trade by prefecture...")
    raw = _fetch(RETAIL_PREF_ID, limit=10000)
    df = _values_to_df(raw)

    if df.empty:
        raise ValueError("Retail prefecture fetch returned no data.")

    df = df.rename(columns={
        "@tab":   "tab",
        "@cat01": "industry_code",
        "@area":  "area_code",
        "@time":  "year_raw",
        "@unit":  "unit",
        "$":      "value",
    })
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"]  = df["year_raw"].str[:4].astype(int)

    result = (df[["year", "area_code", "industry_code", "tab", "unit", "value"]]
              .dropna(subset=["value"])
              .reset_index(drop=True))

    print(f"  Retail by prefecture: {len(result):,} records")
    return result


# ── 3. Wholesale/Retail by Industry ───────────────────────────
def get_retail_by_industry() -> pd.DataFrame:
    """
    Fetch annual wholesale/retail sales by industry group.
    Combines 2023 and 2024 datasets.
    Returns columns: year, area_code, industry_code, tab, value
    """
    print("Fetching retail by industry (2023 + 2024)...")
    frames = []
    for ds_id, year_label in [(RETAIL_IND_23_ID, 2023), (RETAIL_IND_24_ID, 2024)]:
        raw = _fetch(ds_id, limit=5000)
        df  = _values_to_df(raw)
        if df.empty:
            print(f"  No data for {year_label}")
            continue
        df = df.rename(columns={
            "@tab":   "tab",
            "@cat01": "industry_code",
            "@area":  "area_code",
            "@time":  "year_raw",
            "$":      "value",
        })
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["year"]  = year_label
        frames.append(df)

    result = (pd.concat(frames, ignore_index=True)
              [["year", "area_code", "industry_code", "tab", "value"]]
              .dropna(subset=["value"])
              .reset_index(drop=True))

    print(f"  Retail by industry: {len(result):,} records")
    return result


# ── Save all to DuckDB ────────────────────────────────────────
def load_estat_to_duckdb():
    """Fetch all e-Stat datasets and save to DuckDB."""
    import duckdb
    DB_PATH = "data/olist_ecommerce.duckdb"
    con = duckdb.connect(DB_PATH)

    cpi     = get_cpi_monthly()
    retail_pref = get_retail_by_prefecture()
    retail_ind  = get_retail_by_industry()

    for name, df in [
        ("estat_cpi",            cpi),
        ("estat_retail_pref",    retail_pref),
        ("estat_retail_industry", retail_ind),
    ]:
        con.execute(f"DROP TABLE IF EXISTS {name}")
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM df")
        print(f"  Saved → {name} ({len(df):,} rows)")

    con.close()
    print("\nAll e-Stat tables saved to DuckDB.")


if __name__ == "__main__":
    load_estat_to_duckdb()