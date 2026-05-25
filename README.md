# E-Commerce Sales Analytics Pipeline

## Project overview
End-to-end data engineering pipeline processing 1M+ rows of real UK
e-commerce transaction data (Online Retail II, UCI / Kaggle).
Covers ingestion, transformation, warehousing, and BI dashboards.

## Tech stack
| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow |
| Warehouse | PostgreSQL + Snowflake (free tier) |
| Transformation | dbt Core |
| Visualization | Power BI + Tableau Public |
| Language | Python 3.12 |

## Dataset summary
- Source: Online Retail II (UCI) via Kaggle
- Rows: 1,067,371 | Columns: 8
- Date range: Dec 2009 – Dec 2011
- Countries: 43
- Unique customers: 5,942
- Unique products:  5,305

## Data quality findings
| Issue | Count | Handling |
|---|---|---|
| Missing Customer ID | 243,007 | Assigned synthetic ID |
| Cancelled invoices (C prefix) | 8,292 | Filtered to separate table |
| Negative quantities | 22,950 | Linked to cancellations |
| Zero-price rows | 6,207 | Excluded from revenue calc |
| Full duplicate rows | 34,335 | De-duplicated in ETL |

## ETL pipeline

| Table          | Rows loaded |
|---|---|
| dim_geography  | 38          |
| dim_product    | ~4,070      |
| dim_customer   | ~5,900      |
| dim_date       | 1,461       |
| fact_orders    | ~1,047,000  |

Pipeline runtime: ~2 min on local machine.
Re-run with: `python etl/run_pipeline.py`

## Architecture


## Orchestration

Scheduled daily at 02:00 UTC via Apache Airflow 2.9.1.

| Task              | Description                            |
|---|---|
| check_source      | Verify CSV exists and is > 1MB         |
| extract_data      | Read CSV, push row count via XCom      |
| validate_data     | Gate: must have > 900k rows            |
| transform_and_load| Full ETL pipeline                      |
| data_quality_check| Verify warehouse table counts          |
| notify_success    | Log run summary                        |

Start the stack: `docker compose up -d`
Airflow UI: http://localhost:8080 (admin/admin)
