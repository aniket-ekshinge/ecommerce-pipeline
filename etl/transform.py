import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

GUEST_ID_START = 90000000

def transform(df: pd.DataFrame) -> dict:
    """
    Clean raw data and build all dimension + fact DataFrames.
    Returns a dict with keys: geography, product, customer, fact_orders, stats
    """
    logger.info("Starting transform...")
    raw_count = len(df)

    df = df.copy()

    # ── Step 1: Remove full duplicate rows ────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Removed {before - len(df):,} duplicate rows")

    # ── Step 2: Fix StockCode — drop non-product codes ────────────
    invalid_codes = ['POST', 'D', 'M', 'BANK CHARGES', 'PADS', 'DOT', 'CRUK']
    df = df[~df['StockCode'].isin(invalid_codes)]
    df = df[df['StockCode'].str.match(r'^[A-Za-z0-9]+$', na=False)]

    # ── Step 3: Fix Price — remove zero/negative ──────────────────
    before = len(df)
    df = df[df['Price'] > 0]
    logger.info(f"Removed {before - len(df):,} rows with Price <= 0")

    # ── Step 4: Handle cancellations ──────────────────────────────
    df['is_cancelled'] = df['Invoice'].str.startswith('C', na=False)
    # Keep cancellations in the data but flag them; remove negative qty rows
    # that are NOT cancellations (data errors)
    df = df[~((df['Quantity'] < 0) & (~df['is_cancelled']))]
    # For cancelled rows, make quantity positive for storage
    df.loc[df['is_cancelled'], 'Quantity'] = df.loc[df['is_cancelled'], 'Quantity'].abs()

    # ── Step 5: Handle missing Customer IDs ───────────────────────
    df['is_guest'] = df['Customer ID'].isna()
    # Assign ALL guests the same single ID: 0
    df.loc[df['is_guest'], 'Customer ID'] = '0'
    df['Customer ID'] = df['Customer ID'].astype(str).str.strip()
    df['customer_id_int'] = pd.to_numeric(
        df['Customer ID'].str.replace(r'\.0$', '', regex=True),
        errors='coerce'
    ).fillna(0).astype(int)
    logger.info(f"Assigned guest ID 0 to {df['is_guest'].sum():,} rows")

    # ── Step 6: Date features ─────────────────────────────────────
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['date_id'] = df['InvoiceDate'].dt.strftime('%Y%m%d').astype(int)

    # ── Step 7: Revenue ───────────────────────────────────────────
    df['revenue'] = (df['Quantity'] * df['Price']).round(2)

    logger.info(f"Transform complete: {raw_count:,} → {len(df):,} clean rows")

    # ── Build dim_geography ───────────────────────────────────────
    REGION_MAP = {
        'United Kingdom': 'Western Europe',
        'Germany': 'Western Europe', 'France': 'Western Europe',
        'Spain': 'Western Europe', 'Netherlands': 'Western Europe',
        'Belgium': 'Western Europe', 'Switzerland': 'Western Europe',
        'Portugal': 'Western Europe', 'Italy': 'Western Europe',
        'Norway': 'Northern Europe', 'Sweden': 'Northern Europe',
        'Denmark': 'Northern Europe', 'Finland': 'Northern Europe',
        'Iceland': 'Northern Europe', 'Lithuania': 'Northern Europe',
        'Poland': 'Central Europe', 'Czech Republic': 'Central Europe',
        'Austria': 'Central Europe',
        'Cyprus': 'Southern Europe', 'Greece': 'Southern Europe',
        'Malta': 'Southern Europe',
        'USA': 'North America', 'Canada': 'North America',
        'Australia': 'Oceania', 'Japan': 'Asia',
        'Singapore': 'Asia', 'Hong Kong': 'Asia',
        'Israel': 'Middle East', 'Lebanon': 'Middle East',
        'Bahrain': 'Middle East', 'Saudi Arabia': 'Middle East',
        'United Arab Emirates': 'Middle East',
        'Brazil': 'South America',
        'South Africa': 'Africa', 'Nigeria': 'Africa',
    }
    CONTINENT_MAP = {
        'Western Europe': 'Europe', 'Northern Europe': 'Europe',
        'Central Europe': 'Europe', 'Southern Europe': 'Europe',
        'North America': 'Americas', 'South America': 'Americas',
        'Asia': 'Asia', 'Middle East': 'Asia',
        'Oceania': 'Oceania', 'Africa': 'Africa',
    }
    geo = pd.DataFrame({'country': df['Country'].dropna().unique()})
    geo['region'] = geo['country'].map(REGION_MAP).fillna('Other')
    geo['continent'] = geo['region'].map(CONTINENT_MAP).fillna('Other')

    # ── Build dim_product ─────────────────────────────────────────
    product = (
        df[~df['is_cancelled']]
        .groupby('StockCode')
        .agg(
            description=('Description', lambda x: x.mode()[0] if len(x) > 0 else ''),
            avg_price=('Price', 'mean'),
            times_ordered=('Invoice', 'nunique')
        )
        .reset_index()
        .rename(columns={'StockCode': 'stock_code'})
    )
    product['avg_price'] = product['avg_price'].round(2)

    # ── Build dim_customer ────────────────────────────────────────
    cust_agg = (
        df.groupby('customer_id_int')
        .agg(
            country=('Country', 'first'),
            is_guest=('is_guest', 'first'),
            first_order_date=('InvoiceDate', 'min'),
            last_order_date=('InvoiceDate', 'max'),
            total_orders=('Invoice', 'nunique')
        )
        .reset_index()
        .rename(columns={'customer_id_int': 'customer_id'})
    )
    cust_agg['first_order_date'] = cust_agg['first_order_date'].dt.date
    cust_agg['last_order_date']  = cust_agg['last_order_date'].dt.date

    # ── Build fact_orders ─────────────────────────────────────────
    fact = df[[
        'Invoice', 'StockCode', 'customer_id_int', 'date_id',
        'Country', 'Quantity', 'Price', 'revenue', 'is_cancelled'
    ]].rename(columns={
        'Invoice':          'invoice_id',
        'StockCode':        'stock_code',
        'customer_id_int':  'customer_id',
        'Country':          'country',
        'Quantity':         'quantity',
        'Price':            'unit_price',
    })

    valid_codes = set(product['stock_code'].values)
    fact = fact[fact['stock_code'].isin(valid_codes)]

    logger.info(f"fact_orders after FK filter: {len(fact):,} rows")

    stats = {
        'rows_extracted': raw_count,
        'rows_loaded':    len(fact),
        'rows_skipped':   raw_count - len(fact),
    }

    return {
        'geography':   geo,
        'product':     product,
        'customer':    cust_agg,
        'fact_orders': fact,
        'stats':       stats,
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from extract import extract
    raw = extract()
    result = transform(raw)
    for name, df in result.items():
        if isinstance(df, pd.DataFrame):
            print(f"{name}: {len(df):,} rows")