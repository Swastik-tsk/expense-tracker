import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# App Config
# =========================

st.set_page_config(
    page_title="Monthly Budget Dashboard",
    layout="centered",
    page_icon="📊",
)

BUDGET_FILE = "Monthly Budget.csv"
EXPENSE_FILE = "Daily Expense.csv"

BUDGET_REQUIRED_COLUMNS = ["Category", "Budget (₹)"]
EXPENSE_REQUIRED_COLUMNS = ["Date", "Category", "Amount", "Need/Want", "Description"]


# =========================
# Mobile-Friendly Styling
# =========================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 900px;
        }

        div[data-testid="stMetric"] {
            background: #111827;
            border: 1px solid #374151;
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.95rem;
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.45rem;
        }

        div[data-testid="stForm"] {
            border: 1px solid #374151;
            border-radius: 1rem;
            padding: 1rem;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }

            h1 {
                font-size: 1.6rem !important;
            }

            h2, h3 {
                font-size: 1.2rem !important;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.25rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Helpers
# =========================

def ensure_csv_files_exist():
    """Create CSV files with headers if they do not exist."""
    if not os.path.exists(BUDGET_FILE):
        pd.DataFrame(
            [
                {"Category": "Food", "Budget (₹)": 5000},
                {"Category": "Transport", "Budget (₹)": 2000},
                {"Category": "Bills", "Budget (₹)": 4000},
                {"Category": "Entertainment", "Budget (₹)": 1500},
            ]
        ).to_csv(BUDGET_FILE, index=False)

    if not os.path.exists(EXPENSE_FILE):
        pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS).to_csv(EXPENSE_FILE, index=False)


def clean_columns(df):
    df.columns = df.columns.astype(str).str.strip()
    return df


def clean_amount(series):
    return (
        series.astype(str)
        .str.replace(r"[₹,]", "", regex=True)
        .str.strip()
        .replace({"": "0", "nan": "0", "None": "0"})
        .astype(float)
    )


def validate_columns(df, required_columns, file_name):
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing columns in {file_name}: {', '.join(missing_columns)}")
        st.stop()


def load_data():
    ensure_csv_files_exist()

    budget_df = pd.read_csv(BUDGET_FILE)
    expenses_df = pd.read_csv(EXPENSE_FILE)

    budget_df = clean_columns(budget_df)
    expenses_df = clean_columns(expenses_df)

    validate_columns(budget_df, BUDGET_REQUIRED_COLUMNS, BUDGET_FILE)
    validate_columns(expenses_df, EXPENSE_REQUIRED_COLUMNS, EXPENSE_FILE)

    budget_df["Category"] = budget_df["Category"].astype(str).str.strip()
    budget_df["Budget (₹)"] = clean_amount(budget_df["Budget (₹)"])

    if expenses_df.empty:
        expenses_df = pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS)

    expenses_df["Date"] = pd.to_datetime(expenses_df["Date"], errors="coerce")
    expenses_df["Category"] = expenses_df["Category"].astype(str).str.strip()
    expenses_df["Amount"] = clean_amount(expenses_df["Amount"])
    expenses_df["Need/Want"] = expenses_df["Need/Want"].astype(str).str.strip()
    expenses_df["Description"] = expenses_df["Description"].fillna("").astype(str).str.strip()

    return budget_df, expenses_df


def save_expense(new_expense):
    if os.path.exists(EXPENSE_FILE):
        existing_df = pd.read_csv(EXPENSE_FILE)
        existing_df = clean_columns(existing_df)
    else:
        existing_df = pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS)

    existing_df = pd.concat([existing_df, pd.DataFrame([new_expense])], ignore_index=True)
    existing_df.to_csv(EXPENSE_FILE, index=False)


def get_filtered_expenses(expenses_df):
    if expenses_df.empty:
        return expenses_df

    st.sidebar.header("🔎 Filters")

    valid_dates = expenses_df["Date"].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        selected_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_date, end_date = selected_range
            expenses_df = expenses_df[
                (expenses_df["Date"].dt.date >= start_date)
                & (expenses_df["Date"].dt.date <= end_date)
            ]

    categories = sorted(expenses_df["Category"].dropna().unique().tolist())

    selected_categories = st.sidebar.multiselect(
        "Category",
        categories,
        default=categories,
    )

    if selected_categories:
        expenses_df = expenses_df[expenses_df["Category"].isin(selected_categories)]

    need_want_options = sorted(expenses_df["Need/Want"].dropna().unique().tolist())

    selected_need_want = st.sidebar.multiselect(
        "Need/Want",
        need_want_options,
        default=need_want_options,
    )

    if selected_need_want:
        expenses_df = expenses_df[expenses_df["Need/Want"].isin(selected_need_want)]

    return expenses_df


def render_add_expense_form(budget_df):
    st.subheader("➕ Add Daily Expense")

    categories = sorted(budget_df["Category"].dropna().unique().tolist())

    if not categories:
        st.warning("Add categories in Monthly Budget.csv first.")
        return

    with st.form("add_expense_form", clear_on_submit=True):
        expense_date = st.date_input("Date", value=date.today())

        category = st.selectbox(
            "Category",
            categories,
        )

        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=10.0,
            format="%.2f",
        )

        need_want = st.selectbox(
            "Need/Want",
            ["Need", "Want"],
        )

        description = st.text_input(
            "Description",
            placeholder="Example: Lunch, petrol, mobile recharge",
        )

        submitted = st.form_submit_button("Add Expense", use_container_width=True)

        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
                return

            new_expense = {
                "Date": expense_date.strftime("%Y-%m-%d"),
                "Category": category,
                "Amount": amount,
                "Need/Want": need_want,
                "Description": description.strip(),
            }

            save_expense(new_expense)

            st.success("Expense added successfully.")
            st.rerun()


def render_financial_overview(total_budget, total_spent, remaining):
    st.subheader("Financial Overview")

    budget_used_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    st.metric("Total Budget", f"₹{total_budget:,.2f}")
    st.metric("Total Spent", f"₹{total_spent:,.2f}")
    st.metric(
        "Remaining",
        f"₹{remaining:,.2f}",
        delta=f"{budget_used_pct:.2f}% used",
        delta_color="inverse" if remaining < 0 else "normal",
    )


def render_budget_vs_actual(budget_df, expenses_df):
    st.subheader("📈 Budget vs Actual")

    actuals_by_cat = (
        expenses_df.groupby("Category", as_index=False)["Amount"]
        .sum()
        .rename(columns={"Amount": "Calculated Actual (₹)"})
    )

    merged_df = pd.merge(
        budget_df,
        actuals_by_cat,
        on="Category",
        how="left",
    ).fillna(0)

    merged_df["Difference (₹)"] = (
        merged_df["Budget (₹)"] - merged_df["Calculated Actual (₹)"]
    )

    merged_df["Usage %"] = merged_df.apply(
        lambda row: (row["Calculated Actual (₹)"] / row["Budget (₹)"] * 100)
        if row["Budget (₹)"] > 0
        else 0,
        axis=1,
    )

    merged_df["Status"] = merged_df["Difference (₹)"].apply(
        lambda value: "Over Budget" if value < 0 else "Within Budget"
    )

    fig = px.bar(
        merged_df,
        x="Category",
        y=["Budget (₹)", "Calculated Actual (₹)"],
        barmode="group",
        title="Budget vs Actual Spending",
        labels={
            "value": "Amount (₹)",
            "variable": "Metric",
        },
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        merged_df[
            [
                "Category",
                "Budget (₹)",
                "Calculated Actual (₹)",
                "Difference (₹)",
                "Usage %",
                "Status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    over_budget_df = merged_df[merged_df["Difference (₹)"] < 0]

    if not over_budget_df.empty:
        st.error("Overspending detected.")
        st.dataframe(
            over_budget_df[
                [
                    "Category",
                    "Budget (₹)",
                    "Calculated Actual (₹)",
                    "Difference (₹)",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_need_vs_want(expenses_df):
    st.subheader("🧠 Needs vs Wants")

    if expenses_df.empty:
        st.info("No expenses logged yet.")
        return

    need_want_summary = (
        expenses_df.groupby("Need/Want", as_index=False)["Amount"]
        .sum()
    )

    if need_want_summary.empty or need_want_summary["Amount"].sum() <= 0:
        st.info("No Needs/Wants data available yet.")
        return

    fig = px.pie(
        need_want_summary,
        values="Amount",
        names="Need/Want",
        hole=0.4,
        title="Needs vs Wants Split",
        color="Need/Want",
        color_discrete_map={
            "Need": "#2ca02c",
            "Want": "#d62728",
        },
    )

    st.plotly_chart(fig, use_container_width=True)


def render_daily_trend(expenses_df):
    st.subheader("📅 Daily Spending Trend")

    if expenses_df.empty:
        st.info("No expenses logged yet.")
        return

    daily_summary = (
        expenses_df.dropna(subset=["Date"])
        .groupby(expenses_df["Date"].dt.date)["Amount"]
        .sum()
        .reset_index()
        .rename(columns={"Date": "Date"})
    )

    if daily_summary.empty:
        st.info("No valid dates available.")
        return

    fig = px.line(
        daily_summary,
        x="Date",
        y="Amount",
        markers=True,
        title="Daily Expense Trend",
        labels={
            "Amount": "Amount (₹)",
        },
    )

    st.plotly_chart(fig, use_container_width=True)


def render_daily_log(expenses_df):
    st.subheader("📝 Edit Daily Expense Log")

    if expenses_df.empty:
        st.info("No expenses logged yet.")
        return

    editable_df = expenses_df.copy()

    editable_df["Date"] = editable_df["Date"].dt.strftime("%Y-%m-%d")
    editable_df["_Delete"] = False

    edited_df = st.data_editor(
        editable_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.TextColumn("Date", help="Format: YYYY-MM-DD"),
            "Category": st.column_config.TextColumn("Category"),
            "Amount": st.column_config.NumberColumn("Amount", min_value=0.0, step=10.0),
            "Need/Want": st.column_config.SelectboxColumn(
                "Need/Want",
                options=["Need", "Want"],
            ),
            "Description": st.column_config.TextColumn("Description"),
            "_Delete": st.column_config.CheckboxColumn("Delete"),
        },
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes", use_container_width=True):
            cleaned_df = edited_df.copy()

            cleaned_df = cleaned_df[cleaned_df["_Delete"] == False]
            cleaned_df = cleaned_df.drop(columns=["_Delete"])

            cleaned_df["Date"] = pd.to_datetime(
                cleaned_df["Date"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            cleaned_df["Amount"] = clean_amount(cleaned_df["Amount"])
            cleaned_df["Category"] = cleaned_df["Category"].astype(str).str.strip()
            cleaned_df["Need/Want"] = cleaned_df["Need/Want"].astype(str).str.strip()
            cleaned_df["Description"] = cleaned_df["Description"].fillna("").astype(str).str.strip()

            cleaned_df = cleaned_df.dropna(subset=["Date", "Category", "Amount"])

            cleaned_df.to_csv(EXPENSE_FILE, index=False)

            st.success("Daily expenses updated successfully.")
            st.rerun()

    with col2:
        if st.button("↩️ Reload", use_container_width=True):
            st.rerun()


# =========================
# Main App
# =========================

try:
    st.title("📊 Monthly Budget Dashboard")

    budget_df, expenses_df = load_data()
    filtered_expenses_df = get_filtered_expenses(expenses_df)

    total_budget = budget_df["Budget (₹)"].sum()
    total_spent = filtered_expenses_df["Amount"].sum()
    remaining = total_budget - total_spent

    tab_add, tab_dashboard, tab_analysis, tab_log = st.tabs(
        [
            "➕ Add",
            "📊 Dashboard",
            "📈 Analysis",
            "📝 Log",
        ]
    )

    with tab_add:
        render_add_expense_form(budget_df)

    with tab_dashboard:
        render_financial_overview(total_budget, total_spent, remaining)
        st.markdown("---")
        render_budget_vs_actual(budget_df, filtered_expenses_df)

    with tab_analysis:
        render_need_vs_want(filtered_expenses_df)
        st.markdown("---")
        render_daily_trend(filtered_expenses_df)

    with tab_log:
        render_daily_log(expenses_df)

except FileNotFoundError as e:
    st.error("CSV file not found.")
    st.info(f"Missing file: {e.filename}")

except ValueError as e:
    st.error("Invalid data found in CSV.")
    st.info(str(e))

except Exception as e:
    st.error("An unexpected error occurred.")
    st.exception(e)
