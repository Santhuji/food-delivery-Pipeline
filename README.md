# Food Delivery Sales & Profit Analytics

An end-to-end data engineering project that transforms raw food delivery data into structured, analytics-ready datasets using Python, Pandas, and PostgreSQL, with an interactive Streamlit dashboard for exploring sales, profitability, and order performance.

## Project Overview

Food delivery businesses generate large volumes of transactional data across customers, orders, products, and order items. Analyzing this data effectively requires a reliable process for extracting, cleaning, validating, transforming, and storing information.

This project implements a local ETL pipeline that processes food delivery datasets, loads structured data into PostgreSQL, and supports business analysis through SQL queries and an interactive dashboard.

## Key Features

- **ETL Pipeline:** Extracts raw CSV data, transforms datasets using Pandas, and loads the results into PostgreSQL.
- **Data Validation:** Checks data quality and identifies missing or inconsistent values.
- **Relational Database:** Organizes customers, orders, products, and order items into structured tables.
- **SQL Analytics:** Supports sales, revenue, profitability, and order-performance analysis.
- **Interactive Dashboard:** Uses Streamlit and Plotly to visualize key business metrics.
- **Reproducible Workflow:** Separates extraction, transformation, loading, validation, and analytics logic into dedicated files.
- **Credential Protection:** Keeps environment variables and local configuration files out of version control.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | ETL development and data processing |
| Pandas | Data cleaning and transformation |
| PostgreSQL | Relational database and data storage |
| SQL | Business analytics and aggregations |
| Streamlit | Interactive dashboard |
| Plotly | Interactive charts and visualizations |
| pytest | Testing and validation |
| Git and GitHub | Version control |

## Architecture

```text
                Raw CSV Datasets
                       |
                       v
              Data Extraction
                       |
                       v
           Cleaning & Transformation
                  (Pandas)
                       |
                       v
                Data Validation
                       |
                       v
                PostgreSQL DB
                       |
              +--------+--------+
              |                 |
              v                 v
        SQL Analytics     Streamlit App
                                |
                                v
                       Interactive Dashboard
```

## Project Structure

```text
food-delivery-analytics/
│
├── data/
│   ├── raw/                  # Local source CSV files
│   └── processed/            # Local transformed datasets
│
├── dashboard/
│   └── app.py                # Streamlit dashboard
│
├── sql/
│   └── analytics.sql         # Analytical SQL queries
│
├── src/
│   ├── database.py           # PostgreSQL connection
│   ├── generate_data.py      # Synthetic data generation
│   ├── load_data.py          # Data loading logic
│   ├── pipeline.py           # ETL orchestration
│   ├── schema.sql            # Database schema
│   └── validate.py           # Data quality validation
│
├── .env                      # Local environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following before running the project:

- Python 3.10 or later
- PostgreSQL
- Git
- Visual Studio Code or another Python editor

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Santhuji/food-delivery-Pipeline.git
cd food-delivery-Pipeline
```

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt or activate the environment using your preferred Python editor.

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=food_delivery_analytics
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
```

Replace the example username and password with your local PostgreSQL credentials.

**Security:** Never commit `.env` to GitHub. Keep it listed in `.gitignore` and share only a sanitized `.env.example` if configuration documentation is needed.

### 5. Create the PostgreSQL database

Create a database named `food_delivery_analytics` in PostgreSQL.

For example, using `psql`:

```sql
CREATE DATABASE food_delivery_analytics;
```

Ensure the database connection settings in `.env` match your PostgreSQL configuration.

### 6. Run the ETL pipeline

From the project root, execute:

```bash
python src/pipeline.py
```

The pipeline runs the project's ETL workflow and loads the datasets into PostgreSQL according to the implemented pipeline logic.

**Note:** Running the pipeline may replace existing records in its target tables. Back up any data you need before rerunning it.

### 7. Launch the dashboard

```bash
python -m streamlit run dashboard/app.py
```

Streamlit will provide a local URL, typically:

```text
http://localhost:8501
```

Open that address in your browser to explore the dashboard.

## Analytics Use Cases

The project is designed to support analysis such as:

- **Sales Analysis:** Examine revenue across products and order periods.
- **Profitability Analysis:** Evaluate profit and margin using available selling-price, discount, refund, and product-cost data.
- **Order Analysis:** Investigate order volumes and transaction patterns.
- **Product Performance:** Compare product-level sales and profitability.
- **Customer Analysis:** Explore customer purchasing patterns using available customer and order data.
- **Data Quality:** Validate datasets before using them for reporting.

The actual metrics and visualizations depend on the SQL queries and dashboard components implemented in the project.

## Data Model

The project uses four primary entities:

| Table | Description |
|---|---|
| `customers` | Customer-related information |
| `orders` | Order-level transaction details |
| `products` | Product names, brands, and product types |
| `order_items` | Products purchased per order, including quantities, selling prices, discounts, refunds, and product costs |

The relationships between these entities support transactional analysis and product-level profitability calculations.

## Testing and Validation

Run the project's tests with:

```bash
python -m pytest
```

Use the validation module and tests to check data quality and confirm that the ETL workflow behaves as expected.

## Data Privacy

- Raw and processed CSV files are kept locally and excluded from the public repository.
- Environment variables and database credentials must not be committed.
- Use synthetic or appropriately anonymized data when demonstrating the project publicly.

## Future Enhancements

Potential improvements include:

- Schedule ETL runs using Apache Airflow.
- Add incremental loading and change data capture.
- Introduce automated data-quality checks.
- Containerize the application with Docker.
- Deploy the pipeline and database on AWS or another cloud platform.
- Add structured logging, retry handling, and failure alerts.
- Implement larger-scale processing using Apache Spark and PySpark.
- Add CI workflows to automate testing.

## Learning Outcomes

This project demonstrates practical experience with:

- ETL pipeline design and implementation
- Python-based data transformation
- Relational database modeling
- PostgreSQL integration
- SQL-based business analytics
- Data validation and testing
- Dashboard development
- Git-based project organization

## Author

**Santhosh Kumar G**

- GitHub: [@Santhuji](https://github.com/Santhuji)

---

*Built as a hands-on project to develop practical data engineering skills through data ingestion, transformation, database loading, validation, and analytics.*
