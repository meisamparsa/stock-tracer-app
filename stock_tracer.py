import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid

# Streamlit app configuration
st.set_page_config(page_title="Stock Ticker Tracer", layout="wide")

# Title and description
st.title("Stock Ticker Weekly Analysis")
st.write("Analyze a stock's performance on a specific day of the week over a selected date range.")

# User inputs
col1, col2 = st.columns([1, 1])
with col1:
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL").upper()
with col2:
    day_of_week = st.selectbox("Select Day of the Week", 
                              ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], 
                              index=4)  # Default to Friday

# Date range selection
st.subheader("Select Date Range")
col3, col4 = st.columns([1, 1])
default_end = datetime.today()
default_start = default_end - timedelta(weeks=52)
with col3:
    start_date = st.date_input("Start Date", value=default_start, min_value=datetime(2000, 1, 1), max_value=datetime.today())
with col4:
    end_date = st.date_input("End Date", value=default_end, min_value=start_date, max_value=datetime.today())

# Convert day of week to numerical (Monday=0, Sunday=6)
days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
selected_day = days_map[day_of_week]

# Fetch stock data
@st.cache_data
def fetch_stock_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    return df

try:
    # Load data
    df = fetch_stock_data(ticker, start_date, end_date)

    if df.empty:
        st.error("No data found for the provided ticker or date range. Please check the ticker symbol or adjust the dates.")
    else:
        # Filter for selected day of the week
        df['DayOfWeek'] = df.index.dayofweek
        df_filtered = df[df['DayOfWeek'] == selected_day].copy()

        if df_filtered.empty:
            st.warning(f"No data available for {ticker} on {day_of_week}s in the selected date range.")
        else:
            # Calculate high-low variance
            df_filtered['Variance'] = df_filtered['High'] - df_filtered['Low']

            # Select and rename columns for display
            display_df = df_filtered[['Open', 'High', 'Low', 'Close', 'Volume', 'Variance']]
            display_df = display_df.round(2)

            # Display data table
            st.subheader(f"{ticker} Performance on {day_of_week}s ({start_date} to {end_date})")
            st.dataframe(display_df, use_container_width=True)

            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df_filtered.index,
                open=df_filtered['Open'],
                high=df_filtered['High'],
                low=df_filtered['Low'],
                close=df_filtered['Close'],
                name=ticker
            )])

            # Customize chart
            fig.update_layout(
                title=f"{ticker} Candlestick Chart on {day_of_week}s",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                xaxis_rangeslider_visible=False,
                height=600,
                template="plotly_white"
            )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)

            # Summary statistics
            st.subheader("Summary Statistics")
            summary = {
                "Average Open": round(display_df['Open'].mean(), 2),
                "Average Close": round(display_df['Close'].mean(), 2),
                "Average Variance": round(display_df['Variance'].mean(), 2),
                "Max High": round(display_df['High'].max(), 2),
                "Min Low": round(display_df['Low'].min(), 2)
            }
            st.write(summary)

except Exception as e:
    st.error(f"Error fetching data: {str(e)}. Please check the ticker symbol or date range.")