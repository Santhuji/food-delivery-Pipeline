
from pathlib import Path
import pandas as pd
from database import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"


def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    items = pd.read_csv(DATA_DIR / "order_items.csv")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                TRUNCATE TABLE order_items, orders, products, customers
                RESTART IDENTITY CASCADE
            """)

            for _, row in customers.iterrows():
                cur.execute(
                    "INSERT INTO customers (customer_id, customer_name) VALUES (%s, %s)",
                    (int(row["customer_id"]), row["customer_name"])
                )

            for _, row in products.iterrows():
                cur.execute(
                    """
                    INSERT INTO products
                    (product_id, product_name, brand, product_type)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        int(row["product_id"]),
                        row["product_name"],
                        row["brand"],
                        row["product_type"]
                    )
                )

            for _, row in orders.iterrows():
                cur.execute(
                    """
                    INSERT INTO orders
                    (order_id, order_datetime, customer_id, delivery_area, order_status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        int(row["order_id"]),
                        row["order_datetime"],
                        int(row["customer_id"]),
                        row["delivery_area"],
                        row["order_status"]
                    )
                )

            for _, row in items.iterrows():
                cur.execute(
                    """
                    INSERT INTO order_items
                    (order_item_id, order_id, product_id, quantity,
                     unit_selling_price, discount_amount, refund_amount,
                     unit_product_cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        int(row["order_item_id"]),
                        int(row["order_id"]),
                        int(row["product_id"]),
                        int(row["quantity"]),
                        float(row["unit_selling_price"]),
                        float(row["discount_amount"]),
                        float(row["refund_amount"]),
                        float(row["unit_product_cost"])
                    )
                )

    print("Data loaded successfully!")


if __name__ == "__main__":
    load_data()
