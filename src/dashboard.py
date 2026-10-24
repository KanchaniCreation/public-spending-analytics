
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Public Spending Analytics",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# 2. CUSTOM STYLING
# =====================================================

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        padding: 16px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    h1, h2, h3 {
        letter-spacing: -0.4px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. HEADER
# =====================================================

st.title("📊 Public Spending Analytics")

st.markdown(
    "### Education Grants, School Resources & Data Insights"
)

st.caption(
    "An interactive exploratory analytics dashboard "
    "built using Python, Pandas, Streamlit and Plotly."
)

# =====================================================
# 4. PATHS AND DATASETS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

csv_files = sorted(DATA_DIR.glob("*_cleaned.csv"))

if not csv_files:
    st.error("No cleaned CSV files found in data/processed.")
    st.stop()


@st.cache_data
def load_data(file_path, modified_time):
    data = pd.read_csv(file_path, low_memory=False)
    data.columns = data.columns.astype(str).str.strip()
    return data


# =====================================================
# 5. SIDEBAR
# =====================================================

st.sidebar.title("🎛️ Dashboard Controls")

selected_file = st.sidebar.selectbox(
    "Select dataset",
    csv_files,
    format_func=lambda file: file.name
)

try:
    df = load_data(
        str(selected_file),
        selected_file.stat().st_mtime
    )
except Exception as error:
    st.error(f"Could not load dataset: {error}")
    st.stop()

if df.empty:
    st.warning("The selected dataset is empty.")
    st.stop()

# =====================================================
# 6. NUMERIC CONVERSION
# =====================================================

df = df.copy()

for column in df.columns:
    if df[column].dtype == "object":
        converted = pd.to_numeric(df[column], errors="coerce")

        non_missing = df[column].notna().sum()

        if non_missing > 0:
            conversion_rate = converted.notna().sum() / non_missing

            if conversion_rate >= 0.95:
                df[column] = converted

# =====================================================
# 7. DYNAMIC FILTERS
# =====================================================

st.sidebar.header("🔎 Filters")

filtered_df = df.copy()

preferred_filters = [
    "state",
    "district",
    "rural_urban",
    "school_category",
    "school_type",
    "management"
]

available_filters = [
    column for column in preferred_filters
    if column in df.columns
]

# If preferred filters are absent, discover suitable
# categorical columns dynamically.
if not available_filters:
    available_filters = [
        column for column in df.columns
        if (
            df[column].dtype == "object"
            or isinstance(df[column].dtype, pd.CategoricalDtype)
        )
        and 1 < df[column].nunique(dropna=True) <= 50
        and "id" not in column.lower()
        and "code" not in column.lower()
        and "pseudo" not in column.lower()
    ][:4]

for column in available_filters:
    values = sorted(
        df[column].dropna().astype(str).unique().tolist()
    )

    selected_values = st.sidebar.multiselect(
        f"Filter: {column.replace('_', ' ').title()}",
        options=values,
        key=f"filter_{column}"
    )

    if selected_values:
        filtered_df = filtered_df[
            filtered_df[column].astype(str).isin(selected_values)
        ]

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# =====================================================
# 8. IDENTIFY NUMERIC COLUMNS
# =====================================================

all_numeric_columns = filtered_df.select_dtypes(
    include="number"
).columns.tolist()

# Exclude likely identifiers from default numeric analysis.
identifier_keywords = [
    "id",
    "code",
    "pseudo",
    "serial",
    "index"
]

numeric_columns = [
    column for column in all_numeric_columns
    if not any(
        keyword in column.lower()
        for keyword in identifier_keywords
    )
    and filtered_df[column].nunique(dropna=True) > 1
]

# =====================================================
# 9. KPI CARDS
# =====================================================

st.header("📌 Dataset Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Records",
    f"{len(filtered_df):,}"
)

k2.metric(
    "Total Variables",
    f"{filtered_df.shape[1]:,}"
)

k3.metric(
    "Analysis Variables",
    f"{len(numeric_columns):,}"
)

missing_cells = int(filtered_df.isna().sum().sum())

k4.metric(
    "Missing Cells",
    f"{missing_cells:,}"
)

st.caption(f"Dataset: {selected_file.name}")

st.divider()

# =====================================================
# 10. DATA PREVIEW
# =====================================================

with st.expander("📋 Explore Dataset"):
    st.dataframe(
        filtered_df.head(100),
        width="stretch"
    )

    st.download_button(
        "⬇️ Download Filtered Dataset",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_dataset.csv",
        mime="text/csv"
    )

# =====================================================
# 11. GOVERNMENT GRANTS ANALYSIS
# =====================================================


st.header("💰 Government Grants Analysis")

grant_candidates = [
    "grants_receipt",
    "grants_expenditure"
]

grant_columns = [
    col for col in grant_candidates
    if col in filtered_df.columns
]

if grant_columns:

    grant_data = filtered_df[grant_columns].copy()

    for col in grant_columns:
        grant_data[col] = pd.to_numeric(
            grant_data[col], errors="coerce"
        )

    receipt = grant_data.get("grants_receipt")
    expenditure = grant_data.get("grants_expenditure")

    if receipt is not None and expenditure is not None:

        comparison = pd.DataFrame({
            "Grants Received": receipt,
            "Grants Expenditure": expenditure
        })

        # Keep only records with both values for paired analysis.
        comparison = comparison.dropna().copy()

        if comparison.empty:
            st.warning(
                "No records contain both grants receipt and "
                "expenditure values."
            )

        else:
            comparison["Receipt − Expenditure"] = (
                comparison["Grants Received"]
                - comparison["Grants Expenditure"]
            )

            total_receipt = comparison["Grants Received"].sum()
            total_expenditure = comparison["Grants Expenditure"].sum()
            total_difference = (
                total_receipt - total_expenditure
            )

            records = len(comparison)
            expenditure_higher = (
                comparison["Grants Expenditure"]
                > comparison["Grants Received"]
            ).sum()

            equal_records = (
                comparison["Grants Expenditure"]
                == comparison["Grants Received"]
            ).sum()

            # KPI cards
            st.subheader("📌 Grant Overview")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Recorded Receipts",
                f"{total_receipt:,.0f}"
            )

            c2.metric(
                "Recorded Expenditure",
                f"{total_expenditure:,.0f}"
            )

            c3.metric(
                "Receipt − Expenditure",
                f"{total_difference:,.0f}"
            )

            c4.metric(
                "Records Analysed",
                f"{records:,}"
            )

            if total_receipt != 0:
                ratio = total_expenditure / total_receipt * 100
                st.metric(
                    "Expenditure / Receipt",
                    f"{ratio:.2f}%"
                )

            st.caption(
                "Totals use records with both receipt and expenditure "
                "values. Interpret them according to the dataset's "
                "units, coverage and reporting definitions."
            )

            # Automatically generated observations
            st.subheader("💡 Key Data Insights")

            i1, i2, i3 = st.columns(3)

            i1.metric(
                "Expenditure > Receipt",
                f"{expenditure_higher:,}",
                help="Number of records where recorded expenditure "
                     "exceeds recorded receipts."
            )

            i2.metric(
                "Equal Receipt & Expenditure",
                f"{equal_records:,}"
            )

            i3.metric(
                "Positive Difference Records",
                f"{(comparison['Receipt − Expenditure'] > 0).sum():,}",
                help="Records where recorded receipts exceed "
                     "recorded expenditure."
            )

            st.info(
                f"Among {records:,} records with both values, "
                f"{expenditure_higher:,} have expenditure greater "
                f"than receipts, while {equal_records:,} have equal "
                "recorded receipts and expenditure. These are "
                "record-level observations, not proof of fund misuse "
                "or unspent balances."
            )

            # Scatter plot
            st.subheader("📊 Receipt vs. Expenditure")

            fig = px.scatter(
                comparison,
                x="Grants Received",
                y="Grants Expenditure",
                title="Recorded Grant Values by Record",
                template="plotly_white",
                opacity=0.65,
                hover_data=[
                    "Receipt − Expenditure"
                ]
            )

            fig.update_layout(height=450)

            st.plotly_chart(
                fig,
                width="stretch"
            )

            # Difference distribution
            st.subheader("📉 Receipt–Expenditure Difference")

            fig = px.histogram(
                comparison,
                x="Receipt − Expenditure",
                nbins=30,
                title="Distribution of Recorded Differences",
                template="plotly_white"
            )

            fig.update_layout(height=400)

            st.plotly_chart(
                fig,
                width="stretch"
            )

            # Flag unusually high values for investigation
            st.subheader("🔎 Potentially Unusual Records")

            difference = comparison["Receipt − Expenditure"]

            q1 = difference.quantile(0.25)
            q3 = difference.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            unusual = comparison[
                (difference < lower_bound)
                | (difference > upper_bound)
            ]

            st.write(
                f"Records flagged for review using the IQR rule: "
                f"**{len(unusual):,}**"
            )

            st.caption(
                "Statistical flags are not evidence of errors or "
                "misuse. They identify records that may deserve "
                "further investigation."
            )

            with st.expander("View grant comparison table"):
                st.dataframe(
                    comparison.head(100),
                    width="stretch"
                )

            # Download analysed results
            st.download_button(
                label="⬇️ Download Grant Analysis CSV",
                data=comparison.to_csv(index=False).encode("utf-8"),
                file_name="grant_analysis.csv",
                mime="text/csv"
            )

    else:
        selected_grant = grant_columns[0]

        values = pd.to_numeric(
            filtered_df[selected_grant],
            errors="coerce"
        ).dropna()

        c1, c2, c3 = st.columns(3)

        c1.metric("Recorded Total", f"{values.sum():,.0f}")

        c2.metric(
            "Recorded Average",
            f"{values.mean():,.2f}" if not values.empty else "N/A"
        )

        c3.metric("Records with Values", f"{len(values):,}")

        fig = px.histogram(
            x=values,
            nbins=30,
            title=f"Distribution of {selected_grant}",
            template="plotly_white",
            labels={"x": selected_grant}
        )

        st.plotly_chart(fig, width="stretch")

else:
    st.info(
        "This dataset does not contain the configured grants columns. "
        "Select a dataset containing grants_receipt or "
        "grants_expenditure."
    )


# =====================================================
# 12. SCHOOL RESOURCES ANALYSIS
# =====================================================

st.divider()
st.header("🏫 School Resources Analysis")

resource_candidates = [
    "balavatika_located_yn",
    "special_training",
    "material_training",
    "free_text_books_pr",
    "free_uniform_pr",
    "grants_receipt",
    "grants_expenditure"
]

resource_columns = [
    column for column in resource_candidates
    if column in filtered_df.columns
]

if resource_columns:

    selected_resource = st.selectbox(
        "Select a resource or indicator",
        resource_columns,
        key="resource_analysis"
    )

    resource_series = filtered_df[selected_resource]

    resource_counts = (
        resource_series
        .fillna("Missing")
        .astype(str)
        .value_counts()
        .rename_axis("Value")
        .reset_index(name="Records")
    )

    fig = px.bar(
        resource_counts,
        x="Value",
        y="Records",
        color="Value",
        title=f"Recorded Values: {selected_resource}",
        text="Records",
        template="plotly_white"
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Recorded Value",
        yaxis_title="Number of Records"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.caption(
        "The chart shows recorded values, not necessarily the number "
        "of schools possessing a resource. Interpret categories using "
        "the dataset documentation."
    )

else:
    st.info(
        "No configured resource indicators are available in this dataset."
    )

# =====================================================
# 13. AUTOMATIC DESCRIPTIVE INSIGHTS
# =====================================================

st.divider()
st.header("💡 Key Data Insights")

if numeric_columns:

    selected_insight_column = st.selectbox(
        "Choose a variable for insight generation",
        numeric_columns,
        key="insight_variable"
    )

    series = pd.to_numeric(
        filtered_df[selected_insight_column],
        errors="coerce"
    ).dropna()

    if not series.empty:

        i1, i2, i3, i4 = st.columns(4)

        i1.metric(
            "Mean",
            f"{series.mean():,.2f}"
        )

        i2.metric(
            "Median",
            f"{series.median():,.2f}"
        )

        i3.metric(
            "Minimum",
            f"{series.min():,.2f}"
        )

        i4.metric(
            "Maximum",
            f"{series.max():,.2f}"
        )

        zero_count = int((series == 0).sum())

        zero_percentage = (
            zero_count / len(series) * 100
        )

        st.markdown("#### Automatically Generated Findings")

        st.write(
            f"- **Valid observations:** {len(series):,}."
        )

        st.write(
            f"- **Zero-valued observations:** {zero_count:,} "
            f"({zero_percentage:.2f}% of valid observations)."
        )

        st.write(
            f"- **Range:** {series.min():,.2f} to "
            f"{series.max():,.2f}."
        )

        if series.mean() != 0:
            cv = series.std() / abs(series.mean()) * 100

            st.write(
                f"- **Coefficient of variation:** {cv:.2f}%. "
                "A higher value indicates greater variation relative "
                "to the absolute mean."
            )

        st.caption(
            "These are descriptive findings, not proof of policy impact "
            "or evidence of misuse. Variable definitions and units matter."
        )

else:
    st.info(
        "No suitable varying numeric columns are available "
        "for automatic descriptive insights."
    )

# =====================================================
# 14. NUMERIC EXPLORATION
# =====================================================

st.divider()
st.header("📈 Interactive Numeric Analysis")

if numeric_columns:

    selected_numeric = st.selectbox(
        "Select numeric variable",
        numeric_columns,
        key="numeric_exploration"
    )

    numeric_series = pd.to_numeric(
        filtered_df[selected_numeric],
        errors="coerce"
    ).dropna()

    if not numeric_series.empty:

        left, right = st.columns(2)

        with left:

            fig = px.histogram(
                numeric_series,
                x=selected_numeric,
                nbins=30,
                title=f"Distribution of {selected_numeric}",
                template="plotly_white"
            )

            st.plotly_chart(
                fig,
                width="stretch"
            )

        with right:

            fig = px.box(
                numeric_series,
                y=selected_numeric,
                title=f"Spread and Potential Outliers: {selected_numeric}",
                template="plotly_white"
            )

            st.plotly_chart(
                fig,
                width="stretch"
            )

        st.subheader("Summary Statistics")

        stats = numeric_series.describe().to_frame(
            name="Value"
        ).round(2)

        st.dataframe(
            stats,
            width="stretch"
        )

    else:
        st.info("No valid numeric observations are available.")

else:
    st.info(
        "No suitable numeric columns are available for analysis."
    )

# =====================================================
# 15. CORRELATION ANALYSIS
# =====================================================

st.divider()
st.header("🔗 Correlation Analysis")

if len(numeric_columns) >= 2:

    correlation_df = filtered_df[numeric_columns].corr()

    fig = px.imshow(
        correlation_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Between Numeric Variables"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.caption(
        "Correlation measures association, not causation. "
        "Only interpret relationships between meaningful variables."
    )

else:
    st.info(
        "At least two suitable numeric variables are required "
        "for correlation analysis."
    )

# =====================================================
# 16. DATA QUALITY REPORT
# =====================================================

st.divider()
st.header("🔍 Data Quality Report")

quality_df = pd.DataFrame({
    "Column": filtered_df.columns,
    "Data Type": [
        str(filtered_df[column].dtype)
        for column in filtered_df.columns
    ],
    "Missing Values": [
        int(filtered_df[column].isna().sum())
        for column in filtered_df.columns
    ],
    "Missing Percentage": [
        round(filtered_df[column].isna().mean() * 100, 2)
        for column in filtered_df.columns
    ],
    "Unique Values": [
        int(filtered_df[column].nunique(dropna=True))
        for column in filtered_df.columns
    ]
})

st.dataframe(
    quality_df,
    width="stretch"
)

duplicate_rows = int(filtered_df.duplicated().sum())

q1, q2 = st.columns(2)

q1.metric(
    "Duplicate Rows",
    f"{duplicate_rows:,}"
)

q2.metric(
    "Duplicate Row Percentage",
    f"{duplicate_rows / len(filtered_df) * 100:.2f}%"
)

st.download_button(
    "⬇️ Download Data Quality Report",
    data=quality_df.to_csv(index=False).encode("utf-8"),
    file_name="data_quality_report.csv",
    mime="text/csv"
)

# =====================================================
# 17. FOOTER
# =====================================================

st.divider()

st.caption(
    "Public Spending Analytics | Exploratory analysis "
    "of education-related datasets | Built with Streamlit and Plotly"
)
