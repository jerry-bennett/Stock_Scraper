import streamlit as st
from datetime import datetime, timedelta
from golden_cross import (
    fetch_historical_data,
    detect_crossovers,
    plot_stock_data_with_indicators,
    get_trending_symbols
)

st.title("📈 Golden Cross Stock Scanner")

# Choose mode
mode = st.radio("Choose an option:", ["Specific Stock", "Trending Stocks"])

# Date input shared by both modes
start_date = st.date_input("Start Date", datetime(2024, 1, 1))
end_date = st.date_input("End Date", datetime.today())

# Mode 1: Specific Stock
if mode == "Specific Stock":
    symbol = st.text_input("Stock Symbol", value="AAPL")
    run_button = st.button("Check")

    if run_button and symbol:
        historical_data = fetch_historical_data(symbol.upper(), start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        if historical_data is not None:
            crossovers = detect_crossovers(historical_data)
            golden_crosses = [date for c in crossovers if isinstance(c, tuple) and c[0] == "Golden Cross" for date in [c[1]]]
            death_crosses  = [date for c in crossovers if isinstance(c, tuple) and c[0] == "Death Cross" for date in [c[1]]]

            if golden_crosses:
                st.success(f"✨ Golden Cross detected on {golden_crosses[-1].strftime('%Y-%m-%d')}")
            if death_crosses:
                st.warning(f"⚠️ Death Cross detected on {death_crosses[-1].strftime('%Y-%m-%d')}")

            fig = plot_stock_data_with_indicators(historical_data, symbol.upper(), golden_crosses, death_crosses)
            st.pyplot(fig)
        else:
            st.error("❌ Failed to load data for that stock.")

# Mode 2: Trending Stocks
elif mode == "Trending Stocks":
    max_stocks = st.slider("Max stocks to scan", 1, 25, 10)
    recent_only = st.checkbox("Show only recent crosses (last 30 days)", value=True)
    run_button = st.button("Run Scan")

    if run_button:
        symbols = get_trending_symbols()[:max_stocks]
        recent_cutoff = datetime.today() - timedelta(days=30)

        for symbol in symbols:
            st.subheader(f"🔍 {symbol}")
            data = fetch_historical_data(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

            if data is None or data.empty:
                st.warning(f"⚠️ No data for {symbol}")
                continue

            crossovers = detect_crossovers(data)
            golden_crosses = [date for c in crossovers if isinstance(c, tuple) and c[0] == "Golden Cross" for date in [c[1]]]
            death_crosses  = [date for c in crossovers if isinstance(c, tuple) and c[0] == "Death Cross" for date in [c[1]]]

            if recent_only:
                golden_crosses = [date for date in golden_crosses if date >= recent_cutoff]

            if golden_crosses:
                st.success(f"📈 Golden Cross on {golden_crosses[-1].strftime('%Y-%m-%d')}")
                fig = plot_stock_data_with_indicators(data, symbol, [golden_crosses[-1]], [])
                st.pyplot(fig)
            else:
                st.info("📉 No recent golden cross.")
