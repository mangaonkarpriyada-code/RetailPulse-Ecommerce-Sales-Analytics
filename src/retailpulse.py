"""Reusable data functions for the RetailPulse analytics project."""
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "Online Retail.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

REQUIRED_COLUMNS = [
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country"
]

def load_raw_data(path=DATA_PATH):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run `python download_dataset.py` first."
        )
    df = pd.read_excel(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing expected columns: {missing}")
    return df

def clean_data(df):
    """Return cleaned sales transactions and a dictionary of cleaning counts."""
    work = df.copy()
    initial_rows = len(work)
    work = work.drop_duplicates()
    duplicates_removed = initial_rows - len(work)

    work["InvoiceNo"] = work["InvoiceNo"].astype(str).str.strip()
    work["Quantity"] = pd.to_numeric(work["Quantity"], errors="coerce")
    work["UnitPrice"] = pd.to_numeric(work["UnitPrice"], errors="coerce")
    work["InvoiceDate"] = pd.to_datetime(work["InvoiceDate"], errors="coerce")
    work["CustomerID"] = work["CustomerID"].astype("string").str.replace(r"\.0$", "", regex=True)

    cancelled = work["InvoiceNo"].str.upper().str.startswith("C")
    cancelled_removed = int(cancelled.sum())
    work = work.loc[~cancelled].copy()

    before_valid = len(work)
    work = work.dropna(subset=["InvoiceNo", "StockCode", "Description", "Quantity",
                               "InvoiceDate", "UnitPrice", "Country"])
    missing_required_removed = before_valid - len(work)

    invalid = (work["Quantity"] <= 0) | (work["UnitPrice"] <= 0)
    invalid_removed = int(invalid.sum())
    work = work.loc[~invalid].copy()

    work["Revenue"] = work["Quantity"] * work["UnitPrice"]
    work["InvoiceMonth"] = work["InvoiceDate"].dt.to_period("M").astype(str)
    work["InvoiceDay"] = work["InvoiceDate"].dt.date
    work["CustomerID"] = work["CustomerID"].astype("string")

    stats = {
        "original_rows": initial_rows,
        "duplicates_removed": duplicates_removed,
        "cancelled_invoices_removed": cancelled_removed,
        "rows_missing_required_fields_removed": missing_required_removed,
        "invalid_quantity_or_price_removed": invalid_removed,
        "final_rows": len(work),
    }
    return work.reset_index(drop=True), stats

def build_summary(df):
    total_revenue = float(df["Revenue"].sum())
    total_orders = int(df["InvoiceNo"].nunique())
    identified_customers = int(df["CustomerID"].nunique())
    average_order_value = total_revenue / total_orders if total_orders else 0
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "identified_customers": identified_customers,
        "average_order_value": average_order_value,
        "units_sold": int(df["Quantity"].sum()),
        "countries": int(df["Country"].nunique()),
    }

def export_analysis(df, cleaning_stats):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / "cleaned_online_retail.csv", index=False)
    pd.DataFrame([cleaning_stats]).to_csv(OUTPUT_DIR / "cleaning_summary.csv", index=False)

    monthly = df.groupby("InvoiceMonth", as_index=False).agg(
        Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")
    ).sort_values("InvoiceMonth")
    monthly.to_csv(OUTPUT_DIR / "monthly_sales.csv", index=False)

    products = df.groupby("Description", as_index=False).agg(
        Revenue=("Revenue", "sum"), Quantity=("Quantity", "sum")
    ).sort_values("Revenue", ascending=False)
    products.head(20).to_csv(OUTPUT_DIR / "top_products.csv", index=False)

    countries = df.groupby("Country", as_index=False).agg(
        Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique")
    ).sort_values("Revenue", ascending=False)
    countries.to_csv(OUTPUT_DIR / "country_sales.csv", index=False)

    customers = df.dropna(subset=["CustomerID"]).groupby("CustomerID", as_index=False).agg(
        Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"),
        Units=("Quantity", "sum")
    ).sort_values("Revenue", ascending=False)
    customers.head(20).to_csv(OUTPUT_DIR / "top_customers.csv", index=False)

    return monthly, products, countries, customers
