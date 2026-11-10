
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="RetailPulse | Sales & Customer Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# LIGHT BLUE AND WHITE THEME
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f3f8ff;
    }

    [data-testid="stSidebar"] {
        background-color: #e8f2ff;
    }

    h1, h2, h3 {
        color: #17365d;
    }

    .main-title {
        font-size: 34px;
        font-weight: 750;
        color: #17365d;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #7185a2;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 700;
        color: #17365d;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 13px;
        border: 1px solid #dceaff;
        box-shadow: 0 3px 12px rgba(38, 90, 150, 0.06);
    }

    .metric-label {
        color: #7185a2;
        font-size: 14px;
        font-weight: 600;
    }

    .metric-value {
        color: #17365d;
        font-size: 25px;
        font-weight: 750;
        margin-top: 7px;
    }

    .insight-card {
        background-color: white;
        border-left: 4px solid #38a6e8;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        color: #29415f;
        box-shadow: 0 2px 8px rgba(38, 90, 150, 0.05);
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dceaff;
        border-radius: 10px;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background-color: #1677c8;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 18px;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background-color: #105b9a;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# DATA LOADING AND CLEANING
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"

CLEANED_FILE = OUTPUT_DIR / "cleaned_online_retail.csv"
RAW_FILE = DATA_DIR / "Online Retail.xlsx"


@st.cache_data
def load_data():

    if CLEANED_FILE.exists():
        df = pd.read_csv(CLEANED_FILE)

    elif RAW_FILE.exists():
        df = pd.read_excel(RAW_FILE)

    else:
        return None

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Convert data types
    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(
            df["InvoiceDate"],
            errors="coerce"
        )

    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(
            df["Quantity"],
            errors="coerce"
        )

    if "UnitPrice" in df.columns:
        df["UnitPrice"] = pd.to_numeric(
            df["UnitPrice"],
            errors="coerce"
        )

    if "CustomerID" in df.columns:
        df["CustomerID"] = pd.to_numeric(
            df["CustomerID"],
            errors="coerce"
        )

    # Calculate revenue if it does not exist
    if "Revenue" not in df.columns:
        df["Revenue"] = df["Quantity"] * df["UnitPrice"]

    # Remove invalid records
    required_columns = [
        "InvoiceNo",
        "InvoiceDate",
        "Quantity",
        "UnitPrice",
        "Country"
    ]

    df = df.dropna(subset=required_columns)

    df = df[
        (df["Quantity"] > 0) &
        (df["UnitPrice"] > 0)
    ].copy()

    df["Revenue"] = (
        df["Quantity"] * df["UnitPrice"]
    )

    # Create month column
    df["InvoiceMonth"] = (
        df["InvoiceDate"].dt.to_period("M").astype(str)
    )

    return df


df = load_data()

if df is None:
    st.error(
        "Dataset not found. Please place Online Retail.xlsx "
        "inside the data folder or cleaned_online_retail.csv "
        "inside the outputs folder."
    )
    st.stop()

if df.empty:
    st.error("The dataset contains no valid records.")
    st.stop()


# --------------------------------------------------
# DASHBOARD HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">RetailPulse</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'E-commerce Sales & Customer Insights | '
    'Final Data Analytics Project – SWYNEX Internship'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("Dashboard Filters")
st.sidebar.caption("Customize your analysis")

min_date = df["InvoiceDate"].min().date()
max_date = df["InvoiceDate"].max().date()

selected_dates = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

countries = sorted(
    df["Country"].dropna().unique().tolist()
)

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=countries,
    default=countries
)

st.sidebar.divider()

st.sidebar.info(
    "Use the filters to explore sales performance "
    "and customer purchasing patterns."
)


# --------------------------------------------------
# FILTER DATA
# --------------------------------------------------

filtered = df[
    (df["InvoiceDate"].dt.date >= start_date) &
    (df["InvoiceDate"].dt.date <= end_date) &
    (df["Country"].isin(selected_countries))
].copy()

if filtered.empty:
    st.warning(
        "No records found for the selected filters. "
        "Please change your date range or country selection."
    )
    st.stop()


# --------------------------------------------------
# KEY PERFORMANCE INDICATORS
# --------------------------------------------------

total_revenue = filtered["Revenue"].sum()

total_orders = filtered["InvoiceNo"].nunique()

total_customers = filtered["CustomerID"].nunique()

total_units = filtered["Quantity"].sum()

average_order_value = (
    total_revenue / total_orders
    if total_orders > 0 else 0
)

st.markdown(
    '<div class="section-title">Business Overview</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4 = st.columns(4)


def metric_card(column, label, value):

    column.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


metric_card(k1, "Total Revenue", f"£{total_revenue:,.2f}")
metric_card(k2, "Total Orders", f"{total_orders:,}")
metric_card(k3, "Total Customers", f"{total_customers:,}")
metric_card(k4, "Units Sold", f"{total_units:,.0f}")

st.write("")

k5, k6 = st.columns(2)

metric_card(
    k5,
    "Average Order Value",
    f"£{average_order_value:,.2f}"
)

metric_card(
    k6,
    "Countries",
    f"{filtered['Country'].nunique():,}"
)


# --------------------------------------------------
# MONTHLY SALES ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Monthly Sales Analysis</div>',
    unsafe_allow_html=True
)

monthly = (
    filtered.groupby("InvoiceMonth")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique")
    )
    .reset_index()
    .sort_values("InvoiceMonth")
)

c1, c2 = st.columns(2)

with c1:

    fig = px.line(
        monthly,
        x="InvoiceMonth",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Trend",
        template="plotly_white",
        color_discrete_sequence=["#1677c8"]
    )

    fig.update_layout(
        height=430,
        xaxis_title="Month",
        yaxis_title="Revenue (£)",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


with c2:

    fig = px.bar(
        monthly,
        x="InvoiceMonth",
        y="Orders",
        title="Monthly Order Count",
        template="plotly_white",
        color_discrete_sequence=["#38bdf8"]
    )

    fig.update_layout(
        height=430,
        xaxis_title="Month",
        yaxis_title="Number of Orders",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# PRODUCT ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Product Performance</div>',
    unsafe_allow_html=True
)

products = (
    filtered.groupby("Description")
    .agg(
        Revenue=("Revenue", "sum"),
        Units_Sold=("Quantity", "sum")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
    .head(10)
)

c1, c2 = st.columns(2)

with c1:

    fig = px.bar(
        products.sort_values("Revenue"),
        x="Revenue",
        y="Description",
        orientation="h",
        title="Top 10 Products by Revenue",
        template="plotly_white",
        color_discrete_sequence=["#1677c8"]
    )

    fig.update_layout(
        height=480,
        xaxis_title="Revenue (£)",
        yaxis_title="Product",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


with c2:

    fig = px.bar(
        products.sort_values("Units_Sold"),
        x="Units_Sold",
        y="Description",
        orientation="h",
        title="Top 10 Products by Units Sold",
        template="plotly_white",
        color_discrete_sequence=["#38bdf8"]
    )

    fig.update_layout(
        height=480,
        xaxis_title="Units Sold",
        yaxis_title="Product",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# COUNTRY-WISE SALES ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Country-wise Sales Analysis</div>',
    unsafe_allow_html=True
)

country_sales = (
    filtered.groupby("Country")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
    .head(10)
)

c1, c2 = st.columns(2)

with c1:

    fig = px.bar(
        country_sales.sort_values("Revenue"),
        x="Revenue",
        y="Country",
        orientation="h",
        title="Top 10 Countries by Revenue",
        template="plotly_white",
        color_discrete_sequence=["#1677c8"]
    )

    fig.update_layout(
        height=450,
        xaxis_title="Revenue (£)",
        yaxis_title="Country",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


with c2:

    fig = px.pie(
        country_sales,
        names="Country",
        values="Revenue",
        title="Revenue Share by Country",
        template="plotly_white",
        hole=0.4
    )

    fig.update_layout(
        height=450,
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# CUSTOMER ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Customer Analysis</div>',
    unsafe_allow_html=True
)

customer_sales = (
    filtered.dropna(subset=["CustomerID"])
    .groupby("CustomerID")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Units_Purchased=("Quantity", "sum")
    )
    .reset_index()
    .sort_values("Revenue", ascending=False)
)

c1, c2 = st.columns(2)

with c1:

    fig = px.bar(
        customer_sales.head(15).sort_values("Revenue"),
        x="Revenue",
        y="CustomerID",
        orientation="h",
        title="Top 15 Customers by Revenue",
        template="plotly_white",
        color_discrete_sequence=["#1677c8"]
    )

    fig.update_layout(
        height=430,
        xaxis_title="Revenue (£)",
        yaxis_title="Customer ID",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)


with c2:

    fig = px.histogram(
        customer_sales,
        x="Revenue",
        nbins=30,
        title="Customer Revenue Distribution",
        template="plotly_white",
        color_discrete_sequence=["#38bdf8"]
    )

    fig.update_layout(
        height=430,
        xaxis_title="Customer Revenue (£)",
        yaxis_title="Number of Customers",
        font=dict(color="#29415f"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff"
    )

    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Top 15 Customers")

st.dataframe(
    customer_sales.head(15),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# AUTOMATIC BUSINESS INSIGHTS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Key Business Insights</div>',
    unsafe_allow_html=True
)

best_month = monthly.loc[monthly["Revenue"].idxmax()]

best_country = (
    country_sales.iloc[0]
    if not country_sales.empty else None
)

best_product = (
    products.iloc[0]
    if not products.empty else None
)

best_customer = (
    customer_sales.iloc[0]
    if not customer_sales.empty else None
)

insights = [
    f"Total revenue generated in the selected period is £{total_revenue:,.2f}.",

    f"The business recorded {total_orders:,} unique orders.",

    f"The highest-revenue month in the selected period was "
    f"{best_month['InvoiceMonth']} with £{best_month['Revenue']:,.2f}.",

    f"The average order value was £{average_order_value:,.2f}.",

    f"A total of {total_customers:,} unique customers made purchases."
]

if best_country is not None:

    insights.append(
        f"{best_country['Country']} generated the highest revenue "
        f"among the top 10 countries: £{best_country['Revenue']:,.2f}."
    )

if best_product is not None:

    insights.append(
        f"The highest-revenue product in the filtered data was "
        f"{best_product['Description']}."
    )

if best_customer is not None:

    insights.append(
        f"Customer {best_customer['CustomerID']} generated the "
        f"highest customer revenue: £{best_customer['Revenue']:,.2f}."
    )

for insight in insights:

    st.markdown(
        f'<div class="insight-card">✦ &nbsp; {insight}</div>',
        unsafe_allow_html=True
    )


# --------------------------------------------------
# TRANSACTION DATA AND DOWNLOAD
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">Transaction Records</div>',
    unsafe_allow_html=True
)

with st.expander("Explore Filtered Transaction Records"):

    st.caption(
        f"Showing up to 500 of {len(filtered):,} filtered records."
    )

    st.dataframe(
        filtered.head(500),
        use_container_width=True,
        hide_index=True
    )

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Transaction Data",
    data=csv,
    file_name="retailpulse_filtered_data.csv",
    mime="text/csv"
)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#8496ad;
        font-size:12px;
        padding:15px;
    ">
        RetailPulse | E-commerce Sales & Customer Insights<br>
        Final Data Analytics Project | SWYNEX Internship<br>
        Built using Python, Pandas, Streamlit and Plotly
    </div>
    """,
    unsafe_allow_html=True
)
