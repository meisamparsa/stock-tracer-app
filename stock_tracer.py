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
st.write("Analyze a stock's performance on a specific day of the week over a selected date range, including technical indicators and analyst insights.")

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

# Fetch stock object for analyst info
@st.cache_resource
def get_stock_object(ticker):
    return yf.Ticker(ticker)

# Calculate Stochastic Oscillator
def calculate_stochastic(df, period=14):
    df['L14'] = df['Low'].rolling(window=period).min()
    df['H14'] = df['High'].rolling(window=period).max()
    df['%K'] = 100 * ((df['Close'] - df['L14']) / (df['H14'] - df['L14']))
    df['%D'] = df['%K'].rolling(window=3).mean()
    return df

# Calculate RSI
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

try:
    # Load data
    df = fetch_stock_data(ticker, start_date, end_date)
    stock = get_stock_object(ticker)

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

            # Calculate technical indicators
            df_filtered = calculate_stochastic(df_filtered)
            df_filtered = calculate_rsi(df_filtered)

            # Select and rename columns for display
            display_df = df_filtered[['Open', 'High', 'Low', 'Close', 'Volume', 'Variance', '%K', '%D', 'RSI']]
            display_df = display_df.round(2)
            # Sort by date descending (most recent at top)
            display_df = display_df.sort_index(ascending=False)

            # Display data table
            st.subheader(f"{ticker} Performance on {day_of_week}s ({start_date} to {end_date})")
            st.dataframe(display_df, use_container_width=True)

            # Create OHLC chart
            fig_ohlc = go.Figure(data=[go.Ohlc(
                x=df_filtered.index,
                open=df_filtered['Open'],
                high=df_filtered['High'],
                low=df_filtered['Low'],
                close=df_filtered['Close'],
                name=ticker
            )])

            # Customize OHLC chart
            fig_ohlc.update_layout(
                title=f"{ticker} Stock OHLC Chart on {day_of_week}s",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                xaxis_rangeslider_visible=False,
                height=600,
                template="plotly_white"
            )

            # Display OHLC chart
            st.plotly_chart(fig_ohlc, use_container_width=True)

            # Create Stochastic Oscillator chart
            fig_stoch = go.Figure()
            fig_stoch.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['%K'], name='%K', line=dict(color='blue')))
            fig_stoch.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['%D'], name='%D', line=dict(color='red')))
            fig_stoch.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_stoch.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Oversold")

            # Customize Stochastic chart
            fig_stoch.update_layout(
                title=f"{ticker} Stochastic Oscillator on {day_of_week}s",
                xaxis_title="Date",
                yaxis_title="Stochastic (%K, %D)",
                height=400,
                template="plotly_white"
            )

            # Display Stochastic chart
            st.plotly_chart(fig_stoch, use_container_width=True)

            # Create RSI chart
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['RSI'], name='RSI', line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")

            # Customize RSI chart
            fig_rsi.update_layout(
                title=f"{ticker} RSI on {day_of_week}s",
                xaxis_title="Date",
                yaxis_title="RSI",
                height=400,
                template="plotly_white"
            )

            # Display RSI chart
            st.plotly_chart(fig_rsi, use_container_width=True)

            # Summary Statistics and Analyst Insights side by side
            st.subheader("Summary and Insights")
            col5, col6 = st.columns([1, 1])
            
            with col5:
                st.write("**Summary Statistics**")
                summary = {
                    "Average Open": round(display_df['Open'].mean(), 2),
                    "Average Close": round(display_df['Close'].mean(), 2),
                    "Average Variance": round(display_df['Variance'].mean(), 2),
                    "Max High": round(display_df['High'].max(), 2),
                    "Min Low": round(display_df['Low'].min(), 2),
                    "Average %K": round(display_df['%K'].mean(), 2) if not display_df['%K'].isna().all() else "N/A",
                    "Average %D": round(display_df['%D'].mean(), 2) if not display_df['%D'].isna().all() else "N/A",
                    "Average RSI": round(display_df['RSI'].mean(), 2) if not display_df['RSI'].isna().all() else "N/A"
                }
                # Display summary statistics as formatted text
                summary_text = (
                    f"- Average Open: {summary['Average Open']}\n"
                    f"- Average Close: {summary['Average Close']}\n"
                    f"- Average Variance: {summary['Average Variance']}\n"
                    f"- Max High: {summary['Max High']}\n"
                    f"- Min Low: {summary['Min Low']}\n"
                    f"- Average %K: {summary['Average %K']}\n"
                    f"- Average %D: {summary['Average %D']}\n"
                    f"- Average RSI: {summary['Average RSI']}"
                )
                st.markdown(summary_text)

            with col6:
                st.write("**Analyst Insights**")
                try:
                    info = stock.info
                    recommendation = info.get('recommendationKey', 'N/A')
                    price_target = info.get('targetMeanPrice', 'N/A')
                    analyst_recommendation = recommendation.capitalize() if recommendation != 'N/A' else 'N/A'
                    mean_price_target = round(price_target, 2) if isinstance(price_target, (int, float)) else 'N/A'
                    # Display analyst insights as formatted text
                    analyst_text = (
                        f"- Analyst Recommendation: {analyst_recommendation}\n"
                        f"- Mean Price Target: {mean_price_target}"
                    )
                    st.markdown(analyst_text)
                    if analyst_recommendation == 'N/A' or mean_price_target == 'N/A':
                        st.info("Analyst data may not be available for this ticker via yfinance.")
                except:
                    st.info("Unable to fetch analyst recommendations or price target. Data may not be available via yfinance.")

            # Fixed-position PayPal Donate Button
            paypal_button = """
            <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; background-color: #ffffff; padding: 10px; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); opacity: 0.70;">
                <form action="https://www.paypal.com/donate" method="post" target="_blank">
                    <input type="hidden" name="hosted_button_id" value="3YFWRK6PZZVPG" />
                    <input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif" border="0" name="submit" title="Securely donate with PayPal" alt="Donate with PayPal" style="width: 100px; height: auto;" align="center"/>
                    <div style="text-align: center; font-size: 14px; font-family: Arial, sans-serif; color: #003087; margin-top: 5px;">If you like it, would you support me!</div>
                </form>
            </div>
            """
            st.markdown(paypal_button, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error fetching data: {str(e)}. Please check the ticker symbol or date range.")
