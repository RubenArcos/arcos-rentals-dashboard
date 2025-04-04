
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Arcos Rentals Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("Arcos Rentals 2024.xlsx")
    data = pd.concat([xls.parse(sheet) for sheet in xls.sheet_names], ignore_index=True)
    data.columns = data.iloc[0]
    data = data[1:]
    data = data.rename(columns={
        'Date': 'Date',
        'Bank': 'Bank',
        'Account': 'Account',
        'Description': 'Description',
        'Amount': 'Amount',
        'Type': 'Type',
        'Category': 'Category',
        'Entity': 'Entity',
        'Notes': 'Notes'
    })
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data['Amount'] = pd.to_numeric(data['Amount'], errors='coerce')
    data = data.dropna(subset=['Date', 'Amount'])
    data['Month'] = data['Date'].dt.to_period('M').astype(str)
    data['Category Type'] = data['Category'].apply(lambda x: 'Income' if 'income' in str(x).lower() else 'Expense')
    return data

df = load_data()

st.title("🏡 Arcos Rentals Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("🔍 Filters")
    properties = st.multiselect("Select Properties", options=df['Notes'].dropna().unique(), default=df['Notes'].dropna().unique())
    categories = st.multiselect("Select Categories", options=df['Category'].dropna().unique(), default=df['Category'].dropna().unique())
    show_income = st.checkbox("Show Income", value=True)
    show_expense = st.checkbox("Show Expenses", value=True)
    date_range = st.date_input("Select Date Range", [df['Date'].min(), df['Date'].max()])

# Apply filters
filtered_df = df[
    (df['Notes'].isin(properties)) &
    (df['Category'].isin(categories)) &
    (df['Date'] >= pd.to_datetime(date_range[0])) &
    (df['Date'] <= pd.to_datetime(date_range[1]))
]

if not show_income:
    filtered_df = filtered_df[filtered_df['Category Type'] != 'Income']
if not show_expense:
    filtered_df = filtered_df[filtered_df['Category Type'] != 'Expense']

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Income", f"${filtered_df[filtered_df['Category Type'] == 'Income']['Amount'].sum():,.2f}")
col2.metric("💸 Total Expenses", f"${-filtered_df[filtered_df['Category Type'] == 'Expense']['Amount'].sum():,.2f}")
col3.metric("📊 Net Profit", f"${filtered_df['Amount'].sum():,.2f}")

st.divider()

# Monthly Trend
monthly = filtered_df.groupby(['Month', 'Category Type'])['Amount'].sum().reset_index()
fig1 = px.line(monthly, x='Month', y='Amount', color='Category Type', title="📈 Monthly Income vs Expenses", markers=True)
st.plotly_chart(fig1, use_container_width=True)

# Profit by Property
profit_property = filtered_df.groupby('Notes')['Amount'].sum().sort_values()
fig2 = px.bar(profit_property, title="🏠 Net Profit by Property", labels={'value': 'Net Profit ($)', 'Notes': 'Property'})
st.plotly_chart(fig2, use_container_width=True)

# Expenses by Category
expense_df = filtered_df[filtered_df['Category Type'] == 'Expense']
category_spend = expense_df.groupby('Category')['Amount'].sum().sort_values()
fig3 = px.bar(category_spend, orientation='h', title="🧾 Expenses by Category", labels={'value': 'Total ($)', 'Category': 'Category'})
st.plotly_chart(fig3, use_container_width=True)

# Top Vendors
vendor_freq = filtered_df['Description'].value_counts().nlargest(10)
fig4 = px.bar(vendor_freq, title="🔧 Top Vendors by Transaction Count", labels={'value': 'Transactions', 'index': 'Vendor'})
st.plotly_chart(fig4, use_container_width=True)

# Transaction Table
st.subheader("📋 Transaction Table")
st.dataframe(filtered_df.sort_values("Date", ascending=False), use_container_width=True)
