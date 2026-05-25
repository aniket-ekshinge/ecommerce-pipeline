from datetime import datetime, timedelta
import os
import sys
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

sys.path.insert(0, '/opt/airflow/etl')

DEFAULT_ARGS = {
    'owner':            'data_engineering',
    'depends_on_past':  False,
    'email_on_failure': False,
    'email_on_retry':   False,
    'retries':          2,
    'retry_delay':      timedelta(minutes=5),
}

dag = DAG(
    dag_id='ecommerce_etl_pipeline',
    default_args=DEFAULT_ARGS,
    description='Daily e-commerce ETL: CSV → PostgreSQL star schema',
    schedule='0 2 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ecommerce', 'etl', 'postgres'],
    doc_md="""
    ## E-Commerce ETL Pipeline
    Runs daily at 02:00 UTC. Extracts Online Retail II data,
    transforms it into a star schema, and loads into PostgreSQL.
    ### Tasks
    1. **check_source** — verify CSV file exists and has content
    2. **extract_data** — read CSV into memory, return row count
    3. **validate_data** — check minimum row count threshold
    4. **transform_and_load** — run full ETL, load all tables
    5. **data_quality_check** — verify warehouse row counts
    6. **notify_success** — log completion summary
    """,
)


def check_source_file(**context):
    """Verify the source CSV exists and is non-empty."""
    csv_path = '/opt/airflow/data/raw/online_retail_II.csv'
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Source file not found: {csv_path}")
    size_mb = os.path.getsize(csv_path) / 1e6
    if size_mb < 1:
        raise ValueError(f"Source file too small: {size_mb:.1f}MB — may be corrupted")
    logging.info(f"Source file OK: {size_mb:.1f}MB at {csv_path}")
    context['ti'].xcom_push(key='source_size_mb', value=round(size_mb, 1))


def extract_data(**context):
    """Extract CSV into memory and push row count via XCom."""
    import pandas as pd
    csv_path = '/opt/airflow/data/raw/online_retail_II.csv'
    logging.info("Reading CSV...")
    df = pd.read_csv(
        csv_path,
        encoding='ISO-8859-1',
        dtype={'Invoice': str, 'StockCode': str,
               'Customer ID': str, 'Country': str},
        parse_dates=['InvoiceDate']
    )
    row_count = len(df)
    logging.info(f"Extracted {row_count:,} rows")
    context['ti'].xcom_push(key='raw_row_count', value=row_count)
    return row_count


def validate_data(**context):
    """Fail the DAG if we extracted fewer rows than expected."""
    ti = context['ti']
    row_count = ti.xcom_pull(task_ids='extract_data', key='raw_row_count')
    MIN_EXPECTED = 900_000
    if row_count < MIN_EXPECTED:
        raise ValueError(
            f"Data quality gate failed: got {row_count:,} rows, "
            f"expected at least {MIN_EXPECTED:,}"
        )
    logging.info(f"Validation passed: {row_count:,} rows >= {MIN_EXPECTED:,}")


def transform_and_load(**context):
    """Run the full ETL pipeline."""
    from extract import extract
    from transform import transform
    from load import load
    from db_connection import get_engine

    logging.info("Starting transform + load...")
    engine = get_engine()
    raw_df = extract()
    transformed = transform(raw_df)
    stats = load(engine, transformed)

    context['ti'].xcom_push(key='etl_stats', value=str(stats))
    logging.info(f"ETL complete: {stats}")
    return stats['rows_loaded']


def data_quality_check(**context):
    """Verify expected row counts in the warehouse after load."""
    from db_connection import get_engine
    from sqlalchemy import text

    engine = get_engine()
    checks = {
        'dim_geography': 10,
        'dim_product':   1000,
        'dim_customer':  100,
        'dim_date':      1000,
        'fact_orders':   500_000,
    }
    failed = []
    with engine.connect() as conn:
        for table, min_rows in checks.items():
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")
            ).scalar()
            status = "PASS" if count >= min_rows else "FAIL"
            logging.info(f"  {table}: {count:,} rows [{status}]")
            if count < min_rows:
                failed.append(f"{table} has {count:,} (expected >= {min_rows:,})")

    if failed:
        raise ValueError("Quality checks failed:\n" + "\n".join(failed))
    logging.info("All data quality checks passed.")


def notify_success(**context):
    """Log a summary of the completed run."""
    ti = context['ti']
    stats_str = ti.xcom_pull(task_ids='transform_and_load', key='etl_stats')
    source_mb = ti.xcom_pull(task_ids='check_source', key='source_size_mb')
    raw_rows  = ti.xcom_pull(task_ids='extract_data',  key='raw_row_count')
    logging.info("=" * 50)
    logging.info("PIPELINE COMPLETED SUCCESSFULLY")
    logging.info(f"  Source file:    {source_mb}MB")
    logging.info(f"  Rows extracted: {raw_rows:,}")
    logging.info(f"  ETL stats:      {stats_str}")
    logging.info(f"  Run date:       {context['ds']}")
    logging.info("=" * 50)


with dag:
    t_check = PythonOperator(
        task_id='check_source',
        python_callable=check_source_file,
    )
    t_extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
    )
    t_validate = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
    )
    t_load = PythonOperator(
        task_id='transform_and_load',
        python_callable=transform_and_load,
        execution_timeout=timedelta(minutes=30),
    )
    t_quality = PythonOperator(
        task_id='data_quality_check',
        python_callable=data_quality_check,
    )
    t_notify = PythonOperator(
        task_id='notify_success',
        python_callable=notify_success,
    )

    t_check >> t_extract >> t_validate >> t_load >> t_quality >> t_notify