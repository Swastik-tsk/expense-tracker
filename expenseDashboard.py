import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# Page Setup
# =========================

st.set_page_config(
    page_title="Monthly Budget Dashboard",
    layout="wide",
    page_icon="📊",
)

st.title("📊 Monthly Budget Dashboard")

BUDGET_FILE = "Monthly Budget.csv"
EXPENSE_FILE = "Daily Expense.csv"

BUDGET_REQUIRED_COLUMNS = ["Category", "Budget (₹)"]
EXPENSE_REQUIRED_COLUMNS = ["Date", "Category", "Amount", "Need/Want", "Description"]


# =========================
# Responsive CSS
# =========================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1200px;
            padding-top: 1rem;
            padding-left: clamp(0.75rem, 3vw, 2rem);
            padding-right: clamp(0.75rem, 3vw, 2rem);
            padding-bottom: 2rem;
        }

        h1 {
            font-size: clamp(1.45rem, 4vw, 2.2rem) !important;
            line-height: 1.2;
        }

        h2, h3 {
            font-size: clamp(1.1rem, 3vw, 1.5rem) !important;
        }

        .responsive-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 0.85rem;
            margin: 1rem 0;
        }

        .metric-card {
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 1rem;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

        .metric-label {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            color: #111827;
            font-size: clamp(1.2rem, 4vw, 1.75rem);
            font-weight: 700;
            line-height: 1.2;
        }

        .metric-sub {
            color: #6b7280;
            font-size: 0.82rem;
            margin-top: 0.35rem;
        }

        .section-card {
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: clamp(0.75rem, 2vw, 1.25rem);
            background: #ffffff;
            margin-bottom: 1rem;
        }

        div[data-testid="stTabs"] button {
            white-space: normal;
            padding-left: 0.65rem;
            padding-right: 0.65rem;
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stDataEditor"] {
            width: 100%;
            overflow-x: auto;
        }

        @media (max-width: 640px) {
            .responsive-card-grid {
                grid-template-columns: 1fr;
            }

            .section-card {
                padding: 0.75rem;
            }

            div[data-testid="stTabs"] button {
                font-size: 0.8rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# Helpers
# =========================

def format_currency(value):
    return f"₹{float(value):,.2f}"


def clean_amount(series):
    cleaned = (
        series.astype(str)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .str.strip()
        .replace({
            "": "0",
            "nan": "0",
            "None": "0",
            "NaN": "0",
        })
    )

    return pd.to_numeric(cleaned, errors="coerce").fillna(0).astype(float)


def validate_columns(df, required_columns, file_name):
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing columns in {file_name}: {', '.join(missing_columns)}")
        st.stop()


def ensure_expense_file_exists():
    if not os.path.exists(EXPENSE_FILE):
        pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS).to_csv(EXPENSE_FILE, index=False)


def load_budget_data():
    if not os.path.exists(BUDGET_FILE):
        st.error(f"Missing file: {BUDGET_FILE}")
        st.stop()

    budget_df = pd.read_csv(BUDGET_FILE)
    budget_df.columns = budget_df.columns.str.strip()

    validate_columns(budget_df, BUDGET_REQUIRED_COLUMNS, BUDGET_FILE)

    budget_df["Category"] = budget_df["Category"].fillna("").astype(str).str.strip()
    budget_df["Budget (₹)"] = clean_amount(budget_df["Budget (₹)"])

    budget_df = budget_df[budget_df["Category"] != ""]

    return budget_df


def load_expense_data():
    ensure_expense_file_exists()

    try:
        expenses_df = pd.read_csv(EXPENSE_FILE)
    except pd.errors.EmptyDataError:
        expenses_df = pd.DataFrame(columns=EXPENSE_REQUIRED_COLUMNS)

    expenses_df.columns = expenses_df.columns.str.strip()

    validate_columns(expenses_df, EXPENSE_REQUIRED_COLUMNS, EXPENSE_FILE)

    expenses_df = expenses_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    expenses_df["Date"] = pd.to_datetime(expenses_df["Date"], errors="coerce")
    expenses_df["Category"] = expenses_df["Category"].fillna("").astype(str).str.strip()
    expenses_df["Amount"] = clean_amount(expenses_df["Amount"])
    expenses_df["Need/Want"] = expenses_df["Need/Want"].fillna("").astype(str).str.strip()
    expenses_df["Description"] = expenses_df["Description"].fillna("").astype(str).str.strip()

    expenses_df = expenses_df[expenses_df["Category"] != ""]
    expenses_df = expenses_df[expenses_df["Amount"] >= 0]

    return expenses_df


def append_expense(new_expense):
    existing_df = load_expense_data()

    new_df = pd.DataFrame([new_expense])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)

    updated_df["Date"] = pd.to_datetime(updated_df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    updated_df = updated_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    updated_df.to_csv(EXPENSE_FILE, index=False)


def save_edited_expenses(edited_df):
    cleaned_df = edited_df.copy()

    if "_Delete" in cleaned_df.columns:
        cleaned_df = cleaned_df[cleaned_df["_Delete"] == False]
        cleaned_df = cleaned_df.drop(columns=["_Delete"])

    cleaned_df = cleaned_df.reindex(columns=EXPENSE_REQUIRED_COLUMNS)

    cleaned_df["Date"] = pd.to_datetime(cleaned_df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    cleaned_df["Category"] = cleaned_df["Category"].fillna("").astype(str).str.strip()
    cleaned_df["Amount"] = clean_amount(cleaned_df["Amount"])
    cleaned_df["Need/Want"] = cleaned_df["Need/Want"].fillna("").astype(str).str.strip()
    cleaned_df["Description"] = cleaned_df["Description"].fillna("").astype(str).str.strip()

    cleaned_df = cleaned_df.dropna(subset=["Date"])
    cleaned_df = cleaned_df[cleaned_df["Date"] != "NaT"]
    cleaned_df = cleaned_df[cleaned_df["Category"] != ""]
    cleaned_df = cleaned_df[cleaned_df["Amount"] > 0]

    cleaned_df.to_csv(EXPENSE_FILE, index=False)


def render_metric_cards(total_budget, total_spent, remaining, budget_used_pct):
    remaining_label = "Safe" if remaining >= 0 else "Overspent"

    st.markdown(
        f"""
        <div class="responsive-card-grid">
            <div class="metric-card">
                <div class="metric-label">Total Budget</div>
                <div class="metric-value">{format_currency(total_budget)}</div>
                <div class="metric-sub">Monthly planned budget</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Total Spent</div>
                <div class="metric-value">{format_currency(total_spent)}</div>
                <div class="metric-sub">{budget_used_pct:.2f}% of budget used</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Remaining</div>
                <div class="metric-value">{format_currency(remaining)}</div>
                <div class="metric-sub">{remaining_label}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Main App
# =========================

try:
    budget_df = load_budget_data()
    expenses_df = load_expense_data()

    categories = sorted(budget_df["Category"].dropna().unique().tolist())

    total_budget = budget_df["Budget (₹)"].sum()
    total_spent = expenses_df["Amount"].sum() if not expenses_df.empty else 0
    remaining = total_budget - total_spent
    budget_used_pct = (total_spent / total_budget * 100) if total_budget > 0 else 0

    render_metric_cards(total_budget, total_spent, remaining, budget_used_pct)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "➕ Add",
            "📊 Budget",
            "📈 Analysis",
            "📝 Edit Log",
        ]
    )

    # =========================
    # Add Expense
    # =========================

    with tab1:
        st.subheader("Add Daily Expense")

        if not categories:
            st.warning("No categories found in Monthly Budget.csv.")
        else:
            with st.form("add_expense_form", clear_on_submit=True):
                expense_date = st.date_input("Date", value=date.today())

                category = st.selectbox("Category", categories)

                amount = st.number_input(
                    "Amount",
                    min_value=0.0,
                    step=10.0,
                    format="%.2f",
                )

                need_want = st.selectbox("Need/Want", ["Need", "Want"])

                description = st.text_input(
                    "Description",
                    placeholder="Example: Lunch, petrol, mobile recharge",
                )

                submitted = st.form_submit_button(
                    "Add Expense",
                    use_container_width=True,
                )

                if submitted:
                    if amount <= 0:
                        st.error("Amount must be greater than 0.")
                    else:
                        append_expense({
                            "Date": expense_date.strftime("%Y-%m-%d"),
                            "Category": category,
                            "Amount": amount,
                            "Need/Want": need_want,
                            "Description": description.strip(),
                        })

                        st.success("Expense added successfully.")
                        st.rerun()

    # =========================
    # Budget vs Actual
    # =========================

    with tab2:
        st.subheader("Budget vs Actual")

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
            how="left",
        ).fillna(0)

        merged_df["Budget (₹)"] = pd.to_numeric(
            merged_df["Budget (₹)"],
            errors="coerce",
        ).fillna(0)

        merged_df["Calculated Actual (₹)"] = pd.to_numeric(
            merged_df["Calculated Actual (₹)"],
            errors="coerce",
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
            axis=1,
        )

        merged_df["Status"] = merged_df["Difference (₹)"].apply(
            lambda value: "Over Budget" if value < 0 else "Within Budget"
        )

        chart_df = merged_df.melt(
            id_vars="Category",
            value_vars=["Budget (₹)", "Calculated Actual (₹)"],
            var_name="Metric",
            value_name="Amount",
        )

        fig_bar = px.bar(
            chart_df,
            x="Category",
            y="Amount",
            color="Metric",
            barmode="group",
            title="Budget vs Actual Spending",
            labels={
                "Amount": "Amount (₹)",
                "Category": "Category",
            },
        )

        fig_bar.update_layout(
            height=420,
            margin=dict(l=10, r=10, t=60, b=10),
            xaxis_tickangle=-25,
            legend_orientation="h",
            legend_yanchor="bottom",
            legend_y=1.02,
            legend_xanchor="right",
            legend_x=1,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

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

    # =========================
    # Analysis
    # =========================

    with tab3:
        st.subheader("Needs vs Wants")

        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            need_want_summary = (
                expenses_df.groupby("Need/Want", as_index=False)["Amount"]
                .sum()
            )

            need_want_summary = need_want_summary[
                need_want_summary["Need/Want"].isin(["Need", "Want"])
            ]

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
                        "Want": "#d62728",
                    },
                )

                fig_pie.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=60, b=10),
                    legend_orientation="h",
                )

                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No Needs/Wants data available yet.")

        st.markdown("---")

        st.subheader("Daily Spending Trend")

        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            trend_df = expenses_df.dropna(subset=["Date"]).copy()

            if trend_df.empty:
                st.info("No valid dates found.")
            else:
                trend_df["Date Only"] = trend_df["Date"].dt.date

                daily_summary = (
                    trend_df.groupby("Date Only", as_index=False)["Amount"]
                    .sum()
                    .rename(columns={"Date Only": "Date"})
                )

                fig_line = px.line(
                    daily_summary,
                    x="Date",
                    y="Amount",
                    markers=True,
                    title="Daily Expense Trend",
                    labels={
                        "Amount": "Amount (₹)",
                    },
                )

                fig_line.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=60, b=10),
                )

                st.plotly_chart(fig_line, use_container_width=True)

    # =========================
    # Edit Log
    # =========================

    with tab4:
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
                        help="Use YYYY-MM-DD format",
                    ),
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=categories,
                    ),
                    "Amount": st.column_config.NumberColumn(
                        "Amount",
                        min_value=0.0,
                        step=10.0,
                    ),
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
                    save_edited_expenses(edited_df)
                    st.success("Daily expenses updated successfully.")
                    st.rerun()

            with col2:
                if st.button("↩️ Reload", use_container_width=True):
                    st.rerun()


except FileNotFoundError as e:
    st.error("CSV file not found.")
    st.info(f"Missing file: {e.filename}")

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")