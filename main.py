import streamlit as st
from datetime import datetime
from golden_cross import check_stocks_for_crossovers, get_trending_symbols

st.title("📈 Golden Cross Stock Scanner")

# User input
mode = st.radio("Choose an option:", ["Trending Stocks", "Specific Stock"])

if mode == "Trending Stocks":
    max_stocks = st.slider("Max trending stocks to scan", 1, 20, 10)
    start_date = st.date_input("Start Date", datetime(2024, 1, 1))
    end_date = st.date_input("End Date", datetime.today())
    run_button = st.button("Run Scan")

    if run_button:
        symbols = get_trending_symbols()[:max_stocks]
        check_stocks_for_crossovers(symbols, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

elif mode == "Specific Stock":
    symbol = st.text_input("Stock Symbol", value="AAPL")
    start_date = st.date_input("Start Date", datetime(2024, 1, 1))
    end_date = st.date_input("End Date", datetime.today())
    run_button = st.button("Check")

    if run_button and symbol:
        check_stocks_for_crossovers([symbol], start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
