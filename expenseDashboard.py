import os
from datetime import date

import streamlit as st
import pandas as pd
import plotly.express as px


# =========================
# Page Setup
# =========================

st.set_page_config(
    page_title="Monthly Budget Dashboard",
    layout="centered",
    page_icon="📊"
)

st.title("📊 Monthly Budget Dashboard")

BUDGET_FILE = "Monthly Budget.csv"
EXPENSE_FILE = "Daily Expense.csv"

BUDGET_REQUIRED_COLUMNS = ["Category", "Budget (₹)"]
EXPENSE_REQUIRED_COLUMNS = ["Date", "Category", "Amount", "Need/Want", "Description"]


# =========================
# Mobile Styling
# =========================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 1rem;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid #e5e7eb;
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stForm"] {
            border: 1px solid #e5e7eb;
            border-radius: 1rem;
            padding: 1rem;
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 1.5rem !important;
            }

            h2, h3 {
                font-size: 1.15rem !important;
            }

            div[data-testid="stMetricValue"] {
                font-size: 1.25rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Helper Functions
# =========================

def clean_amount(series):
    return (
        series.astype(str)
        .str.replace(r"[₹,]", "", regex=True)
        .str.strip()
        .replace({"": "0", "nan": "0", "None": "0"})
        .astype(float)
    )


def validate_columns(df, required_columns, file_name):
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing columns in {file_name}: {', '.join(missing)}")
        st.stop()


def append_expense(new_expense):
    if os.path.exists(EXPENSE_FILE):
        existing_df = pd.read_csv(EXPENSE_FILE)
        existing_df.columns = existing_df.columns.str.strip()
    else:
        existing_df = pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS)

    existing_df = existing_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    updated_df = pd.concat(
        [existing_df, pd.DataFrame([new_expense])],
        ignore_index=True
    )

    updated_df.to_csv(EXPENSE_FILE, index=False)


def save_edited_expenses(edited_df):
    cleaned_df = edited_df.copy()

    if "_Delete" in cleaned_df.columns:
        cleaned_df = cleaned_df[cleaned_df["_Delete"] == False]
        cleaned_df = cleaned_df.drop(columns=["_Delete"])

    cleaned_df = cleaned_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    cleaned_df["Date"] = pd.to_datetime(
        cleaned_df["Date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    cleaned_df["Amount"] = clean_amount(cleaned_df["Amount"])
    cleaned_df["Category"] = cleaned_df["Category"].astype(str).str.strip()
    cleaned_df["Need/Want"] = cleaned_df["Need/Want"].astype(str).str.strip()
    cleaned_df["Description"] = cleaned_df["Description"].fillna("").astype(str).str.strip()

    cleaned_df = cleaned_df.dropna(subset=["Date"])
    cleaned_df = cleaned_df[cleaned_df["Category"] != ""]
    cleaned_df = cleaned_df[cleaned_df["Amount"] > 0]

    cleaned_df.to_csv(EXPENSE_FILE, index=False)


try:
    # =========================
    # Read CSV Files
    # =========================

    budget_df = pd.read_csv(BUDGET_FILE)
    expenses_df = pd.read_csv(EXPENSE_FILE)

    budget_df.columns = budget_df.columns.str.strip()
    expenses_df.columns = expenses_df.columns.str.strip()

    validate_columns(budget_df, BUDGET_REQUIRED_COLUMNS, BUDGET_FILE)
    validate_columns(expenses_df, EXPENSE_REQUIRED_COLUMNS, EXPENSE_FILE)

    # =========================
    # Clean Data
    # =========================

    budget_df["Category"] = budget_df["Category"].astype(str).str.strip()
    budget_df["Budget (₹)"] = clean_amount(budget_df["Budget (₹)"])

    expenses_df = expenses_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    if not expenses_df.empty:
        expenses_df["Date"] = pd.to_datetime(expenses_df["Date"], errors="coerce")
        expenses_df["Category"] = expenses_df["Category"].astype(str).str.strip()
        expenses_df["Amount"] = clean_amount(expenses_df["Amount"])
        expenses_df["Need/Want"] = expenses_df["Need/Want"].astype(str).str.strip()
        expenses_df["Description"] = expenses_df["Description"].fillna("").astype(str).str.strip()

    # =========================
    # Calculations
    # =========================

    total_budget = budget_df["Budget (₹)"].sum()
    total_spent = expenses_df["Amount"].sum() if not expenses_df.empty else 0
    remaining = total_budget - total_spent
    budget_used_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    # =========================
    # Top-Level Metrics
    # =========================

    st.header("Financial Overview")

    st.metric("Total Budget", f"₹{total_budget:,.2f}")
    st.metric("Total Spent", f"₹{total_spent:,.2f}")
    st.metric(
        "Remaining",
        f"₹{remaining:,.2f}",
        delta=f"{budget_used_pct:.2f}% used",
        delta_color="inverse" if remaining < 0 else "normal"
    )

    st.markdown("---")

    # =========================
    # Tabs
    # =========================

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Add Expense",
            "📈 Budget vs Actual",
            "📝 Daily Log & Analysis"
        ]
    )

    # =========================
    # Add Expense Tab
    # =========================

    with tab1:
        st.subheader("Add Daily Expense")

        categories = sorted(budget_df["Category"].dropna().unique().tolist())

        with st.form("add_expense_form", clear_on_submit=True):
            expense_date = st.date_input("Date", value=date.today())

            category = st.selectbox(
                "Category",
                categories
            )

            amount = st.number_input(
                "Amount",
                min_value=0.0,
                step=10.0,
                format="%.2f"
            )

            need_want = st.selectbox(
                "Need/Want",
                ["Need", "Want"]
            )

            description = st.text_input(
                "Description",
                placeholder="Example: Lunch, petrol, mobile recharge"
            )

            submitted = st.form_submit_button(
                "Add Expense",
                use_container_width=True
            )

            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    new_expense = {
                        "Date": expense_date.strftime("%Y-%m-%d"),
                        "Category": category,
                        "Amount": amount,
                        "Need/Want": need_want,
                        "Description": description.strip()
                    }

                    append_expense(new_expense)

                    st.success("Expense added successfully.")
                    st.rerun()

    # =========================
    # Budget vs Actual Tab
    # =========================

    with tab2:
        st.subheader("Category Breakdown")

        if expenses_df.empty:
            actuals_by_cat = pd.DataFrame(columns=["Category", "Calculated Actual (₹)"])
        else:
            actuals_by_cat = (
                expenses_df.groupby("Category", as_index=False)["Amount"]
                .sum()
                .rename(columns={"Amount": "Calculated Actual (₹)"})
            )

        merged_df = pd.merge(
            budget_df,
            actuals_by_cat,
            on="Category",
            how="left"
        ).fillna(0)

        merged_df["Difference (₹)"] = (
            merged_df["Budget (₹)"] - merged_df["Calculated Actual (₹)"]
        )

        merged_df["Usage %"] = merged_df.apply(
            lambda row: (
                row["Calculated Actual (₹)"] / row["Budget (₹)"] * 100
                if row["Budget (₹)"] > 0
                else 0
            ),
            axis=1
        )

        merged_df["Status"] = merged_df["Difference (₹)"].apply(
            lambda value: "Over Budget" if value < 0 else "Within Budget"
        )

        fig = px.bar(
            merged_df,
            x="Category",
            y=["Budget (₹)", "Calculated Actual (₹)"],
            barmode="group",
            title="Budget vs Actual Spending per Category",
            labels={
                "value": "Amount (₹)",
                "variable": "Metric"
            }
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
                    "Status"
                ]
            ],
            use_container_width=True,
            hide_index=True
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
                        "Difference (₹)"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

    # =========================
    # Daily Log & Analysis Tab
    # =========================

    with tab3:
        st.subheader("Needs vs Wants")

        if "Need/Want" in expenses_df.columns and not expenses_df.empty:
            need_want_summary = (
                expenses_df.groupby("Need/Want", as_index=False)["Amount"]
                .sum()
            )

            if not need_want_summary.empty and need_want_summary["Amount"].sum() > 0:
                fig_pie = px.pie(
                    need_want_summary,
                    values="Amount",
                    names="Need/Want",
                    hole=0.4,
                    title="Needs vs Wants Split",
                    color="Need/Want",
                    color_discrete_map={
                        "Need": "#2ca02c",
                        "Want": "#d62728"
                    }
                )

                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No Needs/Wants logged yet.")
        else:
            st.info("No expenses logged yet.")

        st.markdown("---")

        st.subheader("Daily Spending Trend")

        if not expenses_df.empty:
            daily_summary = (
                expenses_df.dropna(subset=["Date"])
                .groupby(expenses_df["Date"].dt.date)["Amount"]
                .sum()
                .reset_index()
            )

            daily_summary.columns = ["Date", "Amount"]

            if not daily_summary.empty:
                fig_line = px.line(
                    daily_summary,
                    x="Date",
                    y="Amount",
                    markers=True,
                    title="Daily Expense Trend",
                    labels={
                        "Amount": "Amount (₹)"
                    }
                )

                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No valid dates found.")
        else:
            st.info("No expenses logged yet.")

        st.markdown("---")

        st.subheader("Edit Daily Expense Log")

        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            editable_df = expenses_df.copy()
            editable_df["Date"] = editable_df["Date"].dt.strftime("%Y-%m-%d")
            editable_df["_Delete"] = False

            edited_df = st.data_editor(
                editable_df,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "Date": st.column_config.TextColumn(
                        "Date",
                        help="Use YYYY-MM-DD format"
                    ),
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=categories
                    ),
                    "Amount": st.column_config.NumberColumn(
                        "Amount",
                        min_value=0.0,
                        step=10.0
                    ),
                    "Need/Want": st.column_config.SelectboxColumn(
                        "Need/Want",
                        options=["Need", "Want"]
                    ),
                    "Description": st.column_config.TextColumn("Description"),
                    "_Delete": st.column_config.CheckboxColumn("Delete")
                }
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save Changes", use_container_width=True):
                    save_edited_expenses(edited_df)

                    st.success("Daily expenses updated successfully.")
                    st.rerun()

            with col2:
                if st.button("↩️ Reload", use_container_width=True):
                    st.rerun()

except FileNotFoundError as e:
    st.error("Error: CSV files not found.")
    st.info(f"Missing file: {e.filename}")
    st.info(
        "Make sure 'Monthly Budget.csv' and 'Daily Expense.csv' are in the same folder as this script."
    )

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")