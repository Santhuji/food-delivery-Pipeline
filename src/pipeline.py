
from pathlib import Path
import sys
import time

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

sys.path.insert(0, str(BASE_DIR / "src"))
from database import get_connection

FILES = {
    "customers": "customers.csv",
    "products": "products.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
}

REQUIRED_COLUMNS = {
    "customers": ["customer_id", "customer_name"],
    "products": ["product_id", "product_name", "brand", "product_type"],
    "orders": [
        "order_id", "order_datetime", "customer_id",
        "delivery_area", "order_status"
    ],
    "order_items": [
        "order_item_id", "order_id", "product_id", "quantity",
        "unit_selling_price", "discount_amount",
        "refund_amount", "unit_product_cost"
    ],
}

INSERT_QUERIES = {
    "customers": """
        INSERT INTO customers (customer_id, customer_name)
        VALUES (%s, %s)
    """,
    "products": """
        INSERT INTO products (
            product_id, product_name, brand, product_type
        ) VALUES (%s, %s, %s, %s)
    """,
    "orders": """
        INSERT INTO orders (
            order_id, order_datetime, customer_id,
            delivery_area, order_status
        ) VALUES (%s, %s, %s, %s, %s)
    """,
    "order_items": """
        INSERT INTO order_items (
            order_item_id, order_id, product_id, quantity,
            unit_selling_price, discount_amount,
            refund_amount, unit_product_cost
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """,
}

INSERT_COLUMNS = {
    "customers": ["customer_id", "customer_name"],
    "products": ["product_id", "product_name", "brand", "product_type"],
    "orders": [
        "order_id", "order_datetime", "customer_id",
        "delivery_area", "order_status"
    ],
    "order_items": [
        "order_item_id", "order_id", "product_id", "quantity",
        "unit_selling_price", "discount_amount",
        "refund_amount", "unit_product_cost"
    ],
}


def extract_data():
    print("\n1. EXTRACTING DATA")
    data = {}

    for name, filename in FILES.items():
        path = RAW_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {path}")

        data[name] = pd.read_csv(path)
        print(f"{name}: {len(data[name]):,} rows extracted")

    return data


def transform_data(data):
    print("\n2. TRANSFORMING DATA")

    for name, required in REQUIRED_COLUMNS.items():
        df = data[name].copy()
        df.columns = df.columns.str.strip()

        missing = set(required) - set(df.columns)
        if missing:
            raise ValueError(
                f"{name} is missing columns: {sorted(missing)}"
            )

        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(
                lambda value: value.strip()
                if isinstance(value, str) else value
            )

        data[name] = df

    for name, key in [
        ("customers", "customer_id"),
        ("products", "product_id"),
        ("orders", "order_id"),
        ("order_items", "order_item_id"),
    ]:
        df = data[name]

        if df[key].isna().any():
            raise ValueError(f"{name} contains missing {key} values")

        if df[key].duplicated().any():
            raise ValueError(f"{name} contains duplicate {key} values")

    data["orders"]["order_datetime"] = pd.to_datetime(
        data["orders"]["order_datetime"], errors="raise"
    )

    numeric_columns = {
        "customers": ["customer_id"],
        "products": ["product_id"],
        "orders": ["order_id", "customer_id"],
        "order_items": [
            "order_item_id", "order_id", "product_id", "quantity",
            "unit_selling_price", "discount_amount",
            "refund_amount", "unit_product_cost"
        ],
    }

    for name, columns in numeric_columns.items():
        for col in columns:
            data[name][col] = pd.to_numeric(
                data[name][col], errors="raise"
            )

            if data[name][col].isna().any():
                raise ValueError(f"{name}.{col} contains missing values")

    if (data["order_items"]["quantity"] <= 0).any():
        raise ValueError("Order item quantity must be greater than zero")

    for col in [
        "unit_selling_price", "unit_product_cost",
        "discount_amount", "refund_amount"
    ]:
        if (data["order_items"][col] < 0).any():
            raise ValueError(f"order_items.{col} cannot be negative")

    allowed_statuses = {"delivered", "cancelled", "returned"}
    statuses = set(data["orders"]["order_status"].dropna().unique())

    if not statuses.issubset(allowed_statuses):
        raise ValueError("Orders contain unsupported order statuses")

    if data["orders"]["order_status"].isna().any():
        raise ValueError("Orders contain missing order statuses")

    if not data["orders"]["customer_id"].isin(
        data["customers"]["customer_id"]
    ).all():
        raise ValueError("Orders contain customer IDs not found in customers")

    if not data["order_items"]["order_id"].isin(
        data["orders"]["order_id"]
    ).all():
        raise ValueError("Order items contain unknown order IDs")

    if not data["order_items"]["product_id"].isin(
        data["products"]["product_id"]
    ).all():
        raise ValueError("Order items contain unknown product IDs")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for name, df in data.items():
        df.to_csv(PROCESSED_DIR / FILES[name], index=False)

    print("Transformation and validation completed")
    return data


def load_data(data):
    print("\n3. LOADING DATA INTO POSTGRESQL")

    expected_db = "food_delivery_analytics"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            actual_db = cur.fetchone()[0]

            if actual_db != expected_db:
                raise RuntimeError(
                    f"Wrong database: {actual_db}. "
                    f"Expected {expected_db}. No data loaded."
                )

            cur.execute("""
                TRUNCATE TABLE
                    order_items, orders, products, customers
                RESTART IDENTITY CASCADE
            """)

            for name in [
                "customers", "products", "orders", "order_items"
            ]:
                df = data[name]
                columns = INSERT_COLUMNS[name]

                rows = [
                    tuple(None if pd.isna(value) else value for value in row)
                    for row in df[columns].itertuples(
                        index=False, name=None
                    )
                ]

                if rows:
                    cur.executemany(INSERT_QUERIES[name], rows)

                print(f"{name}: {len(rows):,} rows loaded")

    print("Database transaction committed successfully")


def run_pipeline():
    start = time.time()

    try:
        data = extract_data()
        data = transform_data(data)
        load_data(data)

        print(
            f"\nETL PIPELINE SUCCESSFUL in "
            f"{time.time() - start:.2f} seconds"
        )

    except Exception as error:
        print(f"\nETL PIPELINE FAILED: {error}")
        raise


if __name__ == "__main__":
    run_pipeline()
