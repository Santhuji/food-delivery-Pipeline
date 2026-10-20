
CREATE OR REPLACE VIEW order_item_metrics AS
SELECT
    o.order_id,
    oi.order_item_id,
    o.order_datetime,
    o.customer_id,
    o.delivery_area,
    o.order_status,
    p.product_id,
    p.product_name,
    p.brand,
    p.product_type,
    oi.quantity,
    oi.unit_selling_price,
    oi.unit_product_cost,

    oi.quantity * oi.unit_selling_price AS gross_sales,

    oi.discount_amount,
    oi.refund_amount,

    CASE
        WHEN o.order_status = 'cancelled' THEN 0
        ELSE GREATEST(
            0,
            oi.quantity * oi.unit_selling_price
            - oi.discount_amount
            - oi.refund_amount
        )
    END AS net_sales,

    CASE
        WHEN o.order_status = 'delivered'
        THEN oi.quantity * oi.unit_product_cost
        ELSE 0
    END AS product_cost,

    CASE
        WHEN o.order_status = 'cancelled' THEN 0
        ELSE GREATEST(
            0,
            oi.quantity * oi.unit_selling_price
            - oi.discount_amount
            - oi.refund_amount
        ) -
        CASE
            WHEN o.order_status = 'delivered'
            THEN oi.quantity * oi.unit_product_cost
            ELSE 0
        END
    END AS product_profit,

   CASE
    WHEN o.order_status = 'delivered' THEN oi.quantity
    ELSE 0
END AS units_sold

FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
JOIN products p
    ON oi.product_id = p.product_id;
