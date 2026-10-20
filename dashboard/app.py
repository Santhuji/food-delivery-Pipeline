
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from database import get_connection

st.set_page_config(
    page_title="Food Delivery Analytics",
    page_icon="🍔",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.18);
    }
</style>
""", unsafe_allow_html=True)

st.title("🍔 Food Delivery Analytics")
st.caption("Sales intelligence | Product performance | Customer insights | Profitability")


@st.cache_data(ttl=60)
def load_data():
    query = """
        SELECT *
        FROM order_item_metrics
        WHERE order_status <> 'cancelled'
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load dashboard data: {e}")
    st.stop()

if df.empty:
    st.warning("No data is available in the analytics view.")
    st.stop()

df["order_datetime"] = pd.to_datetime(df["order_datetime"])
df["order_date"] = df["order_datetime"].dt.date

min_date = df["order_date"].min()
max_date = df["order_date"].max()

# -------------------- SIDEBAR FILTERS --------------------

st.sidebar.title("🎛️ Dashboard Controls")

grain = st.sidebar.radio(
    "Reporting period",
    ["Day", "Week", "Month", "Year"],
    horizontal=True,
    key="reporting_grain"
)

if grain == "Day":
    selected_date = st.sidebar.date_input(
        "Select day",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )
    start_date = selected_date
    end_date = selected_date

elif grain == "Week":
    selected_date = st.sidebar.date_input(
        "Choose a date in the week",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )
    start_date = selected_date - pd.Timedelta(days=selected_date.weekday())
    end_date = start_date + pd.Timedelta(days=6)
    st.sidebar.caption(
        f"Week: {start_date:%d %b %Y} – {end_date:%d %b %Y}"
    )

elif grain == "Month":
    months = pd.period_range(
        pd.Timestamp(min_date).to_period("M"),
        pd.Timestamp(max_date).to_period("M"),
        freq="M"
    )
    month_options = list(reversed(months))
    selected_month = st.sidebar.selectbox(
        "Select month",
        month_options,
        format_func=lambda x: x.strftime("%B %Y")
    )
    start_date = selected_month.start_time.date()
    end_date = selected_month.end_time.date()

else:
    years = sorted(
        df["order_datetime"].dt.year.unique().tolist(),
        reverse=True
    )
    selected_year = st.sidebar.selectbox("Select year", years)
    start_date = pd.Timestamp(year=selected_year, month=1, day=1).date()
    end_date = pd.Timestamp(year=selected_year, month=12, day=31).date()

# Keep the selected period inside the available dataset range.
effective_start = max(start_date, min_date)
effective_end = min(end_date, max_date)

st.sidebar.divider()
st.sidebar.caption(
    f"Data available: {min_date:%d %b %Y} to {max_date:%d %b %Y}"
)

category_options = sorted(df["product_type"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Product categories",
    options=category_options,
    default=category_options
)

brand_options = sorted(df["brand"].dropna().unique().tolist())
selected_brands = st.sidebar.multiselect(
    "Brands",
    options=brand_options,
    default=brand_options
)

period_df = df[
    (df["order_date"] >= effective_start)
    & (df["order_date"] <= effective_end)
].copy()

filtered = period_df[
    period_df["product_type"].isin(selected_categories)
    & period_df["brand"].isin(selected_brands)
].copy()

if filtered.empty:
    st.info("No records match the selected period and filters.")
    st.stop()

# -------------------- HELPERS --------------------

def money(value):
    return f"₹{value:,.2f}"


def download_csv(data, filename, label="Download CSV"):
    st.download_button(
        label=label,
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv"
    )


def make_trend(data, value_column):
    data = data.copy()

    if grain == "Day":
        data["trend_period"] = data["order_datetime"].dt.hour
        result = data.groupby("trend_period", as_index=False)[value_column].sum()
        result = result.set_index("trend_period").reindex(range(24), fill_value=0)
        result.index.name = "Hour"
        result = result.reset_index()
        result["Period"] = result["Hour"].astype(str) + ":00"

    elif grain == "Week" or grain == "Month":
        data["trend_period"] = data["order_datetime"].dt.date
        result = data.groupby("trend_period", as_index=False)[value_column].sum()
        result = result.rename(columns={"trend_period": "Period"})
        result["Period"] = result["Period"].astype(str)

    else:
        data["trend_period"] = data["order_datetime"].dt.to_period("M").astype(str)
        result = data.groupby("trend_period", as_index=False)[value_column].sum()
        result = result.rename(columns={"trend_period": "Period"})

    return result


# -------------------- HEADER AND KPIS --------------------

st.subheader(
    f"{grain}ly Report".replace("Dayly", "Daily").replace("Yearly", "Yearly")
)
st.caption(
    f"Showing {effective_start:%d %b %Y} – {effective_end:%d %b %Y}"
)

net_sales = filtered["net_sales"].sum()
order_count = filtered["order_id"].nunique()
units_sold = filtered["units_sold"].sum()
product_profit = filtered["product_profit"].sum()
profit_margin = product_profit / net_sales * 100 if net_sales else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Net Sales", money(net_sales))
c2.metric("🧾 Orders", f"{order_count:,}")
c3.metric("📦 Units Sold", f"{units_sold:,.0f}")
c4.metric("📈 Product Profit", money(product_profit))

c5, c6, c7 = st.columns(3)
c5.metric("Profit Margin", f"{profit_margin:.2f}%")
c6.metric("Customers", f"{filtered['customer_id'].nunique():,}")
c7.metric("Products Sold", f"{filtered.loc[filtered['units_sold'] > 0, 'product_id'].nunique():,}")

st.divider()

# -------------------- SEPARATE DASHBOARD SECTIONS --------------------

tabs = st.tabs([
    "🏠 Overview",
    "📊 Sales & Trends",
    "🥗 Categories",
    "🏆 Products",
    "🏷️ Brands",
    "👥 Customers",
    "📍 Delivery Areas",
    "💹 Profit & Loss",
    "📋 Data Explorer"
])

# 1. OVERVIEW
with tabs[0]:
    st.subheader("Business Performance Overview")

    left, right = st.columns(2)

    with left:
        trend = make_trend(filtered, "net_sales")
        fig = px.line(
            trend,
            x="Period",
            y="net_sales",
            markers=True,
            title=f"Net Sales Trend — {grain}",
            labels={"net_sales": "Net Sales (₹)"}
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        category_sales = (
            filtered.groupby("product_type", as_index=False)["net_sales"]
            .sum()
            .sort_values("net_sales", ascending=False)
        )
        fig = px.pie(
            category_sales,
            names="product_type",
            values="net_sales",
            hole=0.42,
            title="Net Sales Share by Category"
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>Sales: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Products by Net Sales")
    top_products = (
        filtered.groupby("product_name", as_index=False)["net_sales"]
        .sum()
        .sort_values("net_sales", ascending=False)
        .head(5)
    )
    fig = px.bar(
        top_products.sort_values("net_sales"),
        x="net_sales",
        y="product_name",
        orientation="h",
        title="Top 5 Products"
    )
    st.plotly_chart(fig, use_container_width=True)

# 2. SALES AND TRENDS
with tabs[1]:
    st.subheader("Sales Analysis")

    metric_choice = st.selectbox(
        "Choose trend metric",
        ["net_sales", "units_sold", "product_profit"],
        format_func=lambda x: {
            "net_sales": "Net Sales (₹)",
            "units_sold": "Units Sold",
            "product_profit": "Product Profit (₹)"
        }[x]
    )

    trend = make_trend(filtered, metric_choice)
    fig = px.line(
        trend,
        x="Period",
        y=metric_choice,
        markers=True,
        title=f"{metric_choice.replace('_', ' ').title()} by {grain}"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sales by Product Category")
    category_trend = filtered.copy()

    if grain == "Day":
        category_trend["Period"] = category_trend["order_datetime"].dt.hour.astype(str) + ":00"
    elif grain in ["Week", "Month"]:
        category_trend["Period"] = category_trend["order_datetime"].dt.date.astype(str)
    else:
        category_trend["Period"] = category_trend["order_datetime"].dt.to_period("M").astype(str)

    grouped = (
        category_trend.groupby(["Period", "product_type"], as_index=False)["net_sales"]
        .sum()
    )
    fig = px.bar(
        grouped,
        x="Period",
        y="net_sales",
        color="product_type",
        title="Category Sales Trend",
        labels={"net_sales": "Net Sales (₹)", "product_type": "Category"}
    )
    st.plotly_chart(fig, use_container_width=True)

    download_csv(trend, "sales_trend.csv")

# 3. CATEGORY ANALYSIS
with tabs[2]:
    st.subheader("Category Performance")

    category_sales = (
        filtered.groupby("product_type", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            units_sold=("units_sold", "sum"),
            product_profit=("product_profit", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    left, right = st.columns(2)

    with left:
        fig = px.pie(
            category_sales,
            names="product_type",
            values="net_sales",
            hole=0.35,
            title="Sales Share — All Categories"
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.bar(
            category_sales.sort_values("net_sales"),
            x="net_sales",
            y="product_type",
            orientation="h",
            color="product_type",
            title="Net Sales by Category",
            labels={"net_sales": "Net Sales (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Individual Category Analysis")
    chosen_category = st.selectbox(
        "Choose a category",
        sorted(filtered["product_type"].unique())
    )

    category_df = filtered[filtered["product_type"] == chosen_category]
    category_trend = make_trend(category_df, "net_sales")

    left, right = st.columns(2)
    with left:
        fig = px.line(
            category_trend,
            x="Period",
            y="net_sales",
            markers=True,
            title=f"{chosen_category} — Net Sales Trend"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        products_in_category = (
            category_df.groupby("product_name", as_index=False)["net_sales"]
            .sum()
            .sort_values("net_sales", ascending=False)
        )
        fig = px.pie(
            products_in_category,
            names="product_name",
            values="net_sales",
            title=f"{chosen_category} — Product Sales Share"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(category_sales, use_container_width=True, hide_index=True)
    download_csv(category_sales, "category_performance.csv")

# 4. PRODUCTS
with tabs[3]:
    st.subheader("Product Performance")

    product_summary = (
        filtered.groupby(["product_id", "product_name", "product_type"], as_index=False)
        .agg(
            units_sold=("units_sold", "sum"),
            net_sales=("net_sales", "sum"),
            product_profit=("product_profit", "sum")
        )
    )

    left, right = st.columns(2)

    with left:
        top_units = product_summary.sort_values(
            ["units_sold", "net_sales"],
            ascending=[False, False]
        ).head(10)
        fig = px.bar(
            top_units.sort_values("units_sold"),
            x="units_sold",
            y="product_name",
            orientation="h",
            color="product_type",
            title="Top Products by Units Sold"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        top_sales = product_summary.nlargest(10, "net_sales")
        fig = px.bar(
            top_sales.sort_values("net_sales"),
            x="net_sales",
            y="product_name",
            orientation="h",
            title="Top Products by Net Sales"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Product Sales Distribution")
    fig = px.pie(
        product_summary[product_summary["net_sales"] > 0],
        names="product_name",
        values="net_sales",
        title="Product Share of Net Sales"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        product_summary.sort_values("net_sales", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    download_csv(product_summary, "product_performance.csv")

# 5. BRANDS
with tabs[4]:
    st.subheader("Brand Performance")

    brand_summary = (
        filtered.groupby("brand", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            units_sold=("units_sold", "sum"),
            product_profit=("product_profit", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            brand_summary.sort_values("net_sales"),
            x="net_sales",
            y="brand",
            orientation="h",
            title="Brand Net Sales"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            brand_summary,
            names="brand",
            values="net_sales",
            hole=0.4,
            title="Brand Sales Share"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(brand_summary, use_container_width=True, hide_index=True)
    download_csv(brand_summary, "brand_performance.csv")

# 6. CUSTOMERS
with tabs[5]:
    st.subheader("Customer Analytics")

    customer_summary = (
        filtered.groupby("customer_id", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            orders=("order_id", "nunique"),
            units_sold=("units_sold", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    top_customers = customer_summary.head(10)
    fig = px.bar(
        top_customers.sort_values("net_sales"),
        x="net_sales",
        y="customer_id",
        orientation="h",
        title="Top 10 Customers by Net Sales"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Customer Sales Trend")
    customer_ids = customer_summary["customer_id"].head(20).tolist()
    chosen_customer = st.selectbox(
        "Select a customer ID",
        customer_ids
    )
    customer_df = filtered[filtered["customer_id"] == chosen_customer]
    customer_trend = make_trend(customer_df, "net_sales")

    fig = px.line(
        customer_trend,
        x="Period",
        y="net_sales",
        markers=True,
        title=f"Customer {chosen_customer} — Sales Trend"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(customer_summary, use_container_width=True, hide_index=True)
    download_csv(customer_summary, "customer_performance.csv")

# 7. DELIVERY AREAS
with tabs[6]:
    st.subheader("Delivery Area Analysis")

    area_summary = (
        filtered.groupby("delivery_area", as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            orders=("order_id", "nunique"),
            product_profit=("product_profit", "sum")
        )
        .sort_values("net_sales", ascending=False)
    )

    if not area_summary.empty:
        leader = area_summary.iloc[0]
        st.success(
            f"Leading delivery area: {leader['delivery_area']} "
            f"with {money(leader['net_sales'])} in net sales."
        )

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            area_summary.sort_values("net_sales"),
            x="net_sales",
            y="delivery_area",
            orientation="h",
            title="Net Sales by Delivery Area"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            area_summary,
            names="delivery_area",
            values="net_sales",
            title="Delivery Area Sales Share"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(area_summary, use_container_width=True, hide_index=True)
    download_csv(area_summary, "delivery_area_performance.csv")

# 8. PROFIT AND LOSS
with tabs[7]:
    st.subheader("Profitability Analysis")

    profit_by_product = (
        filtered.groupby(["product_id", "product_name"], as_index=False)
        .agg(
            net_sales=("net_sales", "sum"),
            product_cost=("product_cost", "sum"),
            product_profit=("product_profit", "sum")
        )
    )

    profit_by_product["profit_margin_pct"] = (
        profit_by_product["product_profit"]
        .div(profit_by_product["net_sales"].where(profit_by_product["net_sales"] != 0))
        .mul(100)
    )

    left, right = st.columns(2)
    with left:
        most_profitable = profit_by_product.nlargest(10, "product_profit")
        fig = px.bar(
            most_profitable.sort_values("product_profit"),
            x="product_profit",
            y="product_name",
            orientation="h",
            title="Most Profitable Products"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        loss_products = profit_by_product[
            profit_by_product["product_profit"] < 0
        ].nsmallest(5, "product_profit")

        if loss_products.empty:
            st.info("No loss-making products for this selection.")
        else:
            fig = px.bar(
                loss_products.sort_values("product_profit"),
                x="product_profit",
                y="product_name",
                orientation="h",
                title="Top 5 Loss-Making Products"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Product Profit and Margin")
    st.dataframe(
        profit_by_product.sort_values("product_profit", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    download_csv(profit_by_product, "product_profitability.csv")

# 9. DATA EXPLORER
with tabs[8]:
    st.subheader("Filtered Order Item Data")
    st.caption("The rows shown are order items, not unique orders.")

    search = st.text_input("Search product, brand, or category")
    view_df = filtered.copy()

    if search:
        mask = (
            view_df["product_name"].astype(str).str.contains(search, case=False, na=False)
            | view_df["brand"].astype(str).str.contains(search, case=False, na=False)
            | view_df["product_type"].astype(str).str.contains(search, case=False, na=False)
        )
        view_df = view_df[mask]

    st.dataframe(view_df, use_container_width=True, hide_index=True)
    download_csv(view_df, "filtered_order_items.csv", "Download filtered data")

st.divider()
st.caption(
    "Currency: INR (₹). Cancelled orders are excluded. "
    "Units sold are counted for delivered orders. "
    "Profit uses the cost recorded in the analytics view."
)
