
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

brands = ["FreshFarm", "DailyBasket", "UrbanBite", "NatureChoice", "QuickMart", "GoldenHarvest"]
categories = [
    "Fruits",
    "Vegetables",
    "Pulses",
    "Beverages",
    "Snacks",
    "Dairy",
    "Bakery",
    "Staples",
    "Personal Care"
]
areas = ["Indiranagar", "Whitefield", "Koramangala", "Jayanagar", "HSR Layout", "Malleshwaram"]
products = []

for i in range(1, 37):
    category = categories[(i - 1) % len(categories)]
    brand = brands[(i - 1) % len(brands)]
    cost = int(rng.integers(20, 350))
    price = int(cost * rng.uniform(1.05, 1.65))

    if i % 9 == 0:
        price = max(1, int(cost * 0.75))

    products.append({
        "product_id": i,
        "product_name": f"{brand} {category[:-1] if category.endswith('s') else category} {i:02d}",
        "brand": brand,
        "product_type": category,
        "unit_product_cost": cost,
        "unit_selling_price": price
    })

products_df = pd.DataFrame(products)

customers_df = pd.DataFrame({
    "customer_id": range(1, 301),
    "customer_name": [f"Customer {i:03d}" for i in range(1, 301)]
})

orders = []
order_items = []
item_id = 1

start_date = pd.Timestamp("2025-01-01")
end_date = pd.Timestamp("2026-10-01")
days = (end_date - start_date).days

for order_id in range(1, 2501):
    order_date = start_date + pd.Timedelta(
        days=int(rng.integers(0, days)),
        hours=int(rng.integers(8, 23)),
        minutes=int(rng.integers(0, 60))
    )

    status = rng.choice(
        ["delivered", "cancelled", "returned"],
        p=[0.90, 0.07, 0.03]
    )

    orders.append({
        "order_id": order_id,
        "order_datetime": order_date,
        "customer_id": int(rng.integers(1, 301)),
        "delivery_area": rng.choice(areas),
        "order_status": status
    })

    for _ in range(int(rng.integers(1, 5))):
        product = products[int(rng.integers(0, len(products)))]
        quantity = int(rng.integers(1, 6))
        unit_price = product["unit_selling_price"]
        unit_cost = product["unit_product_cost"]
        gross = quantity * unit_price
        discount = round(gross * float(rng.uniform(0, 0.12)), 2)
        refund = round(gross * float(rng.uniform(0.25, 1.0)), 2) if status == "returned" else 0

        order_items.append({
            "order_item_id": item_id,
            "order_id": order_id,
            "product_id": product["product_id"],
            "quantity": quantity,
            "unit_selling_price": unit_price,
            "discount_amount": discount,
            "refund_amount": refund,
            "unit_product_cost": unit_cost
        })
        item_id += 1

orders_df = pd.DataFrame(orders)
items_df = pd.DataFrame(order_items)

orders_df["order_datetime"] = orders_df["order_datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

orders_df.to_csv(DATA_DIR / "orders.csv", index=False)
items_df.to_csv(DATA_DIR / "order_items.csv", index=False)
products_df.to_csv(DATA_DIR / "products.csv", index=False)
customers_df.to_csv(DATA_DIR / "customers.csv", index=False)

print("Dataset generated successfully!")
print(f"Orders: {len(orders_df):,}")
print(f"Order items: {len(items_df):,}")
print(f"Products: {len(products_df):,}")
print(f"Customers: {len(customers_df):,}")
print(f"Output folder: {DATA_DIR}")
