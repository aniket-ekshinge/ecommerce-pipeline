import pandas as pd
import logging
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)
CHUNK_SIZE = 5000

def load(engine, transformed: dict) -> dict:
    start_time = datetime.now()
    stats = transformed['stats'].copy()

    # ── Block 1: Load all dimension tables ───────────────────────
    with engine.begin() as conn:
        logger.info("Loading dim_geography...")
        conn.execute(text("TRUNCATE TABLE dim_geography CASCADE"))
        transformed['geography'].to_sql(
            'dim_geography', conn, if_exists='append', index=False
        )
        geo_count = conn.execute(text("SELECT COUNT(*) FROM dim_geography")).scalar()
        logger.info(f"  dim_geography: {geo_count} rows")

        logger.info("Loading dim_product...")
        conn.execute(text("TRUNCATE TABLE dim_product CASCADE"))
        transformed['product'].to_sql(
            'dim_product', conn, if_exists='append', index=False,
            chunksize=CHUNK_SIZE
        )
        prod_count = conn.execute(text("SELECT COUNT(*) FROM dim_product")).scalar()
        logger.info(f"  dim_product: {prod_count:,} rows")

        logger.info("Loading dim_customer...")
        conn.execute(text("TRUNCATE TABLE dim_customer CASCADE"))
        transformed['customer'].to_sql(
            'dim_customer', conn, if_exists='append', index=False,
            chunksize=CHUNK_SIZE
        )
        cust_count = conn.execute(text("SELECT COUNT(*) FROM dim_customer")).scalar()
        logger.info(f"  dim_customer: {cust_count:,} rows")

    logger.info("Dimensions committed successfully.")

    # ── Block 2: Load fact table separately ──────────────────────
    with engine.begin() as conn:
        logger.info("Loading fact_orders (this takes ~2 minutes)...")
        conn.execute(text("TRUNCATE TABLE fact_orders"))

        # Drop revenue — PostgreSQL generates it automatically
        fact_to_load = transformed['fact_orders'].drop(columns=['revenue'])

        fact_to_load.to_sql(
            'fact_orders', conn,
            if_exists='append', index=False,
            chunksize=CHUNK_SIZE,
            method='multi'
        )
        fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_orders")).scalar()
        logger.info(f"  fact_orders: {fact_count:,} rows")

    logger.info("Fact table committed successfully.")

    # ── Block 3: Write audit log ──────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO etl_log (rows_extracted, rows_loaded, rows_skipped, status, notes)
            VALUES (:extracted, :loaded, :skipped, 'SUCCESS', :notes)
        """), {
            'extracted': stats['rows_extracted'],
            'loaded':    stats['rows_loaded'],
            'skipped':   stats['rows_skipped'],
            'notes':     f"Completed in {elapsed}s"
        })

    logger.info(f"ETL complete in {elapsed}s")
    stats['elapsed_seconds'] = elapsed
    return stats