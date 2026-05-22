import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from db_connection import get_engine
from extract import extract
from transform import transform
from load import load

LOG_FORMAT = '%(asctime)s  %(levelname)-8s  %(name)s — %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etl_run.log', mode='a')
    ]
)
logger = logging.getLogger('pipeline')


def run():
    logger.info("=" * 60)
    logger.info("PIPELINE START")
    logger.info("=" * 60)
    start = datetime.now()

    try:
        # ── Extract ───────────────────────────────────────────────
        logger.info("[1/3] Extract")
        raw_df = extract()

        # ── Transform ─────────────────────────────────────────────
        logger.info("[2/3] Transform")
        transformed = transform(raw_df)
        s = transformed['stats']
        logger.info(
            f"Transform stats — extracted: {s['rows_extracted']:,} | "
            f"to load: {s['rows_loaded']:,} | "
            f"skipped: {s['rows_skipped']:,}"
        )

        # ── Load ──────────────────────────────────────────────────
        logger.info("[3/3] Load")
        engine = get_engine()
        result = load(engine, transformed)

        elapsed = (datetime.now() - start).seconds
        logger.info("=" * 60)
        logger.info(f"PIPELINE SUCCESS — {result['rows_loaded']:,} rows loaded in {elapsed}s")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)