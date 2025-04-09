import logging
import os
from pathlib import Path
import pandas as pd
from data_scrubber import DataScrubber  # Make sure your scrubber class is here

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Column name standardization mapping
COLUMN_STANDARDIZATION = {
    "Invoice ID": "invoice_id",
    "Branch": "branch",
    "City": "city",
    "Customer type": "customer_type",
    "Gender": "gender",
    "Product line": "product_line",
    "Unit price": "unit_price",
    "Quantity": "quantity_sold",
    "Tax 5%": "tax_pct",
    "Total": "total",
    "Date": "date",
    "Time": "time",
    "Payment": "payment_method",
    "cogs": "cost_of_goods_sold",
    "gross margin percentage": "gross_margin_pct",
    "gross income": "gross_income",
    "Rating": "rating"
}

# Expected data types
EXPECTED_DTYPES = {
    "unit_price": "float64",
    "quantity_sold": "int64",
    "tax_pct": "float64",
    "total": "float64",
    "rating": "float64"
}

# File paths
RAW_DATA_DIR = Path("data/raw")
PREPARED_DATA_DIR = Path("data/prepared")
REPORT_DIR = Path("data/report")

# Create output directories if they don't exist
PREPARED_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def process_data(filename: str):
    try:
        df = pd.read_csv(filename)

        # Step 1: Standardize column names
        df = df.rename(columns=COLUMN_STANDARDIZATION)

        # Step 2: Convert expected types
        for column, dtype in EXPECTED_DTYPES.items():
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors='coerce').astype(dtype)

        # Step 3: Merge date + time into datetime
        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
            df.drop(columns=["date", "time"], inplace=True)

        # Step 4: Initialize scrubber and change log
        scrubber = DataScrubber(df)
        change_log = []

        df = scrubber.standardize_column_names()
        change_log.append("Standardized column names.")

        consistency_before = scrubber.check_data_consistency_before_cleaning()
        logger.info(f"Consistency before cleaning: {consistency_before}")
        change_log.append(f"Consistency before cleaning: {consistency_before}")

        df = scrubber.handle_missing_data(drop=True, fill_value=0)
        change_log.append("Dropped rows with missing data or filled with 0.")

        df = scrubber.remove_duplicate_records()
        change_log.append("Removed duplicate records.")

        if "quantity_sold" in df.columns:
            df = scrubber.remove_outliers_zscore("quantity_sold", threshold=3, change_log=change_log)

        consistency_after = scrubber.check_data_consistency_after_cleaning()
        logger.info(f"Consistency after cleaning: {consistency_after}")
        change_log.append(f"Consistency after cleaning: {consistency_after}")

        # Save cleaned data
        prepared_path = PREPARED_DATA_DIR / f"prepared_{Path(filename).stem}.csv"
        df.to_csv(prepared_path, index=False)
        logger.info(f"Cleaned data saved to: {prepared_path}")

        # Save report
        report_path = REPORT_DIR / f"{Path(filename).stem}_report.txt"
        with open(report_path, "w") as report_file:
            report_file.write("\n".join(change_log))
        logger.info(f"Cleaning report saved to: {report_path}")

    except Exception as e:
        logger.error(f"An error occurred while processing {filename}: {e}")
        error_path = REPORT_DIR / f"{Path(filename).stem}_error_report.txt"
        with open(error_path, "w") as error_file:
            error_file.write(str(e))
        logger.info(f"Error report saved to: {error_path}")

def main():
    if not RAW_DATA_DIR.exists():
        logger.error(f"Raw data directory not found: {RAW_DATA_DIR}")
        return

    for file_path in RAW_DATA_DIR.glob("*.csv"):
        logger.info(f"Processing file: {file_path.name}")
        process_data(file_path)

if __name__ == "__main__":
    main()