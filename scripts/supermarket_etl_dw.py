import pandas as pd
import sqlite3
import pathlib
import sys

# For local imports, add project root to sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Constants
DW_DIR = pathlib.Path("data").joinpath("dw")
DB_PATH = DW_DIR.joinpath("supermarket_dw.db")
PREPARED_DATA_DIR = pathlib.Path("data").joinpath("prepared")
PREPARED_FILE = PREPARED_DATA_DIR.joinpath("prepared_supermarket_sales.csv")  # Adjust to match your actual file name

# ---- STEP 1: Create Schema ----
def create_schema(cursor: sqlite3.Cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer (
            customer_id TEXT PRIMARY KEY,
            gender TEXT,
            payment_method TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product (
            product_id TEXT PRIMARY KEY,
            product_line TEXT,
            unit_price REAL,
            tax_pct REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale (
            sale_id TEXT PRIMARY KEY,
            customer_id TEXT,
            product_id TEXT,
            quantity_sold INTEGER,
            total REAL,
            branch TEXT,
            city TEXT,
            datetime TEXT,
            rating REAL,
            FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
            FOREIGN KEY (product_id) REFERENCES product (product_id)
        )
    """)

# ---- STEP 2: Drop Existing Tables ----
def delete_existing_records(cursor: sqlite3.Cursor) -> None:
    cursor.execute("DROP TABLE IF EXISTS sale")
    cursor.execute("DROP TABLE IF EXISTS product")
    cursor.execute("DROP TABLE IF EXISTS customer")
    create_schema(cursor)

# ---- STEP 3: Insert Functions ----
def insert_customers(df: pd.DataFrame, cursor: sqlite3.Cursor) -> None:
    customers = df[['invoice_id', 'gender', 'payment_method']].drop_duplicates()
    customers = customers.rename(columns={'invoice_id': 'customer_id'})
    customers.to_sql("customer", cursor.connection, if_exists="append", index=False)

def insert_products(df: pd.DataFrame, cursor: sqlite3.Cursor) -> None:
    products = df[['invoice_id', 'product_line', 'unit_price', 'tax_pct']].drop_duplicates()
    products = products.rename(columns={'invoice_id': 'product_id'})
    products.to_sql("product", cursor.connection, if_exists="append", index=False)

def insert_sales(df: pd.DataFrame, cursor: sqlite3.Cursor) -> None:
    sales = df[['invoice_id', 'quantity_sold', 'total', 'branch', 'city', 'datetime', 'rating']].copy()
    sales['customer_id'] = sales['invoice_id']
    sales['product_id'] = sales['invoice_id']
    sales = sales.rename(columns={'invoice_id': 'sale_id'})
    sales.to_sql("sale", cursor.connection, if_exists="append", index=False)

# ---- STEP 4: Load and Transform ----
def load_data_to_db() -> None:
    conn = None
    try:
        DW_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        delete_existing_records(cursor)

        df = pd.read_csv(PREPARED_FILE)
        insert_customers(df, cursor)
        insert_products(df, cursor)
        insert_sales(df, cursor)

        conn.commit()
        print("✅ Data successfully loaded into data warehouse.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

# ---- Run the Script ----
if __name__ == "__main__":
    load_data_to_db()
