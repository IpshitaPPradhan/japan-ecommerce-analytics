import pandas as pd
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB_PATH = str(ROOT / "data" / "olist_ecommerce.duckdb")

TABLE_FILES = {
    "orders":       "olist_orders_dataset.csv",
    "order_items":  "olist_order_items_dataset.csv",
    "payments":     "olist_order_payments_dataset.csv",
    "reviews":      "olist_order_reviews_dataset.csv",
    "customers":    "olist_customers_dataset.csv",
    "sellers":      "olist_sellers_dataset.csv",
    "products":     "olist_products_dataset.csv",
    "geolocation":  "olist_geolocation_dataset.csv",
    "categories":   "product_category_name_translation.csv",
}

def load_all():
    con = duckdb.connect(DB_PATH)
    for table, filename in TABLE_FILES.items():
        path = RAW / filename
        if not path.exists():
            print(f"Missing: {filename}")
            continue
        df = pd.read_csv(path)
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM df")
        print(f"OK  {table}: {len(df):,} rows")
    con.close()
    print("\nAll tables loaded into data/olist_ecommerce.duckdb")

def get_con(read_only=False):
    return duckdb.connect(DB_PATH, read_only=read_only)

if __name__ == "__main__":
    load_all()