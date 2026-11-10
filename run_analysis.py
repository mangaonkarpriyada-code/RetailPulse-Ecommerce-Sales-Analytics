"""Run cleaning, analysis and chart export for RetailPulse."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from retailpulse import load_raw_data, clean_data, build_summary, export_analysis, OUTPUT_DIR

def main():
    print("Loading dataset...")
    raw = load_raw_data()
    print(f"Raw rows: {len(raw):,}")

    cleaned, cleaning_stats = clean_data(raw)
    summary = build_summary(cleaned)
    monthly, products, countries, customers = export_analysis(cleaned, cleaning_stats)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(11, 5))
    sns.lineplot(data=monthly, x="InvoiceMonth", y="Revenue", marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Invoice month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "monthly_revenue.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 7))
    top = products.head(10).sort_values("Revenue")
    sns.barplot(data=top, y="Description", x="Revenue")
    plt.title("Top 10 Products by Revenue")
    plt.xlabel("Revenue")
    plt.ylabel("Product")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "top_products.png", dpi=160)
    plt.close()

    plt.figure(figsize=(10, 7))
    top_countries = countries.head(10).sort_values("Revenue")
    sns.barplot(data=top_countries, y="Country", x="Revenue")
    plt.title("Top 10 Countries by Revenue")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "country_revenue.png", dpi=160)
    plt.close()

    print("\\nCLEANING SUMMARY")
    for key, value in cleaning_stats.items():
        print(f"{key}: {value:,}")
    print("\\nBUSINESS KPIs")
    for key, value in summary.items():
        print(f"{key}: {value:,.2f}" if isinstance(value, float) else f"{key}: {value:,}")
    print(f"\\nAnalysis outputs saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
