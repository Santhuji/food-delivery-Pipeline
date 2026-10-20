
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"

orders = pd.read_csv(DATA_DIR / "orders.csv")
items = pd.read_csv(DATA_DIR / "order_items.csv")
products = pd.read_csv(DATA_DIR / "products.csv")
customers = pd.read_csv(DATA_DIR / "customers.csv")

checks = {
    "At least 5,000 order items": len(items) >= 5000,
    "At least 12 months of data": (
        pd.to_datetime(orders["order_datetime"]).max().to_period("M")
        - pd.to_datetime(orders["order_datetime"]).min().to_period("M")
    ).n >= 11,
    "At least 30 products": len(products) >= 30,
    "At least 100 customers": len(customers) >= 100,
    "At least 5 brands": products["brand"].nunique() >= 5,
    "At least 5 categories": products["product_type"].nunique() >= 5,
    "All order items have valid orders": items["order_id"].isin(orders["order_id"]).all(),
    "All order items have valid products": items["product_id"].isin(products["product_id"]).all(),
    "No duplicate order IDs": orders["order_id"].is_unique,
    "No duplicate order item IDs": items["order_item_id"].is_unique,
    "No negative quantities": (items["quantity"] > 0).all(),
}

for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} - {name}")

if not all(checks.values()):
    raise SystemExit("Dataset validation failed. Fix the failed checks before proceeding.")

print("\nAll dataset validation checks passed!")
