import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

RAW_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'raw', 'online_retail_II.csv'
)

EXPECTED_COLUMNS = {
    'Invoice', 'StockCode', 'Description',
    'Quantity', 'InvoiceDate', 'Price', 'Customer ID', 'Country'
}

def extract(filepath: str = RAW_PATH) -> pd.DataFrame:
    """
    Read the raw Online Retail II CSV.
    Returns a DataFrame with original column names and dtypes.
    Raises ValueError if expected columns are missing.
    """
    logger.info(f"Extracting from: {filepath}")

    df = pd.read_csv(
        filepath,
        encoding='ISO-8859-1',
        dtype={
            'Invoice':     str,
            'StockCode':   str,
            'Description': str,
            'Customer ID': str,
            'Country':     str
        },
        parse_dates=['InvoiceDate']
    )

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in source file: {missing}")

    logger.info(f"Extracted {len(df):,} rows, {df.shape[1]} columns")
    logger.info(f"Date range: {df['InvoiceDate'].min()} → {df['InvoiceDate'].max()}")
    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    df = extract()
    print(df.head(3))