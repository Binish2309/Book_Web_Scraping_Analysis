"""
data_cleaning.py
-----------------
Cleans the raw scraped book data (data/raw_books.csv) and produces
data/cleaned_books.csv, ready for EDA and the dashboard.

Run this after scraper.py:
    python data_cleaning.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("data_cleaning")

RAW_PATH = Path("data/raw_books.csv")
CLEAN_PATH = Path("data/cleaned_books.csv")


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw scraped CSV.

    Why: isolating I/O in its own function makes the pipeline testable and
    lets us swap the source (e.g. a sample file) without touching the rest
    of the logic.
    """
    df = pd.read_csv(path)
    logger.info("Loaded %s raw rows from %s", len(df), path)
    return df


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows based on product_url (the natural unique key).

    Why product_url and not title: two different editions can legitimately
    share a title, but each has its own URL on the site, so URL is the
    safer de-duplication key.
    Common beginner mistake: dropping duplicates on title alone, which can
    silently delete distinct books that happen to share a name.
    """
    before = len(df)
    df = df.drop_duplicates(subset="product_url").reset_index(drop=True)
    logger.info("Removed %s duplicate rows", before - len(df))
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing essential fields; fill non-critical gaps.

    Why: title, price_gbp, and product_url are essential -- a row without
    them is not usable for analysis. availability/image_url are
    non-critical and get a safe default instead of losing the whole row.
    """
    before = len(df)
    df = df.dropna(subset=["title", "price_gbp", "product_url"])
    df["availability"] = df["availability"].fillna("Unknown")
    if "image_url" in df.columns:
        df["image_url"] = df["image_url"].fillna("")
    logger.info("Dropped %s rows with missing essential fields", before - len(df))
    return df


def clean_price(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure price is a clean numeric float column.

    Why: prices scraped from HTML sometimes carry currency symbols or stray
    characters (e.g. mis-encoded '£'). This guarantees a pure float column
    for any downstream math (mean, sum, comparisons).
    Common beginner mistake: leaving price as a string -- "£51.77" -- and
    then being unable to sort or average it.
    """
    df["price_gbp"] = (
        df["price_gbp"]
        .astype(str)
        .str.replace("£", "", regex=False)
        .str.replace("Â", "", regex=False)
        .str.strip()
        .astype(float)
    )
    return df


def clean_availability(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise the availability text and derive a boolean in_stock flag."""
    df["availability"] = df["availability"].astype(str).str.strip()
    df["in_stock"] = df["availability"].str.contains("In stock", case=False, na=False)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add analysis-friendly derived columns.

    Why: raw scraped fields are rarely the columns you want to chart
    directly. Binning price into tiers and computing a title-length proxy
    are both common, business-readable derived features.
    """
    df["price_tier"] = pd.cut(
        df["price_gbp"],
        bins=[0, 20, 35, 50, np.inf],
        labels=["Budget (<£20)", "Mid (£20-35)", "Premium (£35-50)", "Luxury (£50+)"],
    )
    df["title_length"] = df["title"].str.len()
    df["title_word_count"] = df["title"].str.split().str.len()
    return df


def validate(df: pd.DataFrame) -> None:
    """Sanity-check the cleaned dataset and log any remaining issues.

    Why: a silent bad value (negative price, empty title) can quietly
    poison every downstream chart. Logging it here surfaces the issue
    immediately instead of someone discovering a weird outlier in a chart
    three steps later.
    """
    assert df["price_gbp"].min() >= 0, "Found a negative price -- check the scraper."
    assert df["title"].str.len().min() > 0, "Found an empty title."
    logger.info("Validation passed: %s clean rows, price range £%.2f-£%.2f",
                len(df), df["price_gbp"].min(), df["price_gbp"].max())


def run_pipeline(input_path: Path = RAW_PATH, output_path: Path = CLEAN_PATH) -> pd.DataFrame:
    df = load_raw(input_path)
    df = drop_duplicates(df)
    df = handle_missing_values(df)
    df = clean_price(df)
    df = clean_availability(df)
    df = engineer_features(df)
    validate(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Saved %s cleaned rows to %s", len(df), output_path)
    return df


if __name__ == "__main__":
    run_pipeline()
