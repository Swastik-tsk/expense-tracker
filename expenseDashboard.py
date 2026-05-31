import streamlit as st
import pandas as pd
import plotly.express as px

# Set up the page
st.set_page_config(page_title="Monthly Budget Dashboard", layout="wide", page_icon="📊")
st.title("📊 Monthly Budget Dashboard")

try:
    # Read directly from the repo's file system! No tokens or URLs needed.
    budget_df = pd.read_csv("Monthly Budget.csv")
    expenses_df = pd.read_csv("Daily Expense.csv")
        
    # Clean column names just in case of trailing spaces
    budget_df.columns = budget_df.columns.str.strip()
    expenses_df.columns = expenses_df.columns.str.strip()

    # --- THE FIX: Clean numbers and force them to match as floats ---
    # Convert to string to safely remove commas/symbols, then convert to float
    budget_df['Budget (₹)'] = budget_df['Budget (₹)'].astype(str).str.replace(r'[₹,]', '', regex=True).astype(float)
    expenses_df['Amount'] = expenses_df['Amount'].astype(str).str.replace(r'[₹,]', '', regex=True).astype(float)
    # ----------------------------------------------------------------

    # --- Calculations ---
    # Calculate actual spend directly from the Daily Expenses log for accuracy
    total_budget = budget_df['Budget (₹)'].sum()
    total_spent = expenses_df['Amount'].sum()
    remaining = total_budget - total_spent

    # --- Top-Level Metrics ---
    st.header("Financial Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget", f"₹{total_budget:,.2f}")
    col2.metric("Total Spent", f"₹{total_spent:,.2f}")
    
    # Color the remaining metric red if negative
    delta_color = "normal" if remaining >= 0 else "inverse"
    col3.metric("Remaining", f"₹{remaining:,.2f}", delta=f"₹{remaining:,.2f}", delta_color=delta_color)
    
    st.markdown("---")

    # --- Tabs for detailed views ---
    tab1, tab2 = st.tabs(["📈 Budget vs Actual", "📝 Daily Log & Analysis"])

    with tab1:
        st.subheader("Category Breakdown")
        
        # Aggregate daily expenses by category
        actuals_by_cat = expenses_df.groupby('Category')['Amount'].sum().reset_index()
        actuals_by_cat.rename(columns={'Amount': 'Calculated Actual (₹)'}, inplace=True)
        
        # Merge budget with calculated actuals
        merged_df = pd.merge(budget_df, actuals_by_cat, on='Category', how='left').fillna(0)
        merged_df['Difference (₹)'] = merged_df['Budget (₹)'] - merged_df['Calculated Actual (₹)']

        # Plotly grouped bar chart
        fig = px.bar(
            merged_df, 
            x='Category', 
            y=['Budget (₹)', 'Calculated Actual (₹)'],
            barmode='group',
            title="Budget vs. Actual Spending per Category",
            labels={'value': 'Amount (₹)', 'variable': 'Metric'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.dataframe(merged_df[['Category', 'Budget (₹)', 'Calculated Actual (₹)', 'Difference (₹)']], use_container_width=True)

    with tab2:
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.subheader("Needs vs Wants")
            if 'Need/Want' in expenses_df.columns:
                need_want_summary = expenses_df.groupby('Need/Want')['Amount'].sum().reset_index()
                
                # Check if there is data to plot to avoid errors on empty files
                if not need_want_summary.empty and need_want_summary['Amount'].sum() > 0:
                    fig_pie = px.pie(
                        need_want_summary, 
                        values='Amount', 
                        names='Need/Want',
                        hole=0.4,
                        color='Need/Want',
                        color_discrete_map={'Need': '#2ca02c', 'Want': '#d62728'}
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No Needs/Wants logged yet.")
        
        with col_right:
            st.subheader("Daily Expense Log")
            st.dataframe(expenses_df, use_container_width=True, hide_index=True)

except FileNotFoundError:
    st.error("Error: CSV files not found!")
    st.info("Make sure 'Monthly Budget.csv' and 'Daily Expenses.csv' are uploaded to your GitHub repository in the exact same folder as this script.")
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")