import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from golden_cross import (
    fetch_historical_data,
    detect_crossovers,
    plot_stock_data_with_indicators,
    get_trending_symbols,
    load_skipped_symbols,
    filter_cooldown_symbols,
    reset_cached_data,
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
            

            if golden_crosses:
                st.success(f"✨ Golden Cross detected on {golden_crosses[-1].strftime('%Y-%m-%d')}")

            fig = plot_stock_data_with_indicators(historical_data, symbol.upper(), golden_crosses)
            st.pyplot(fig)
        else:
            st.error("❌ Failed to load data for that stock.")

# Mode 2: Trending Stocks
elif mode == "Trending Stocks":
    # Get Trending button
    if st.button("📈 Get Trending Symbols"):
        get_trending_symbols()
        st.success("Trending symbols has been set.")

    # Clear button
    if st.button("🧹 Reset Trending Cache"):
        reset_cached_data()
        st.success("Trending cache and skipped symbols have been reset.")

    show_recent_only = st.checkbox("Show only recent crosses (last 30 days)", value=True)
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    if st.button("Start Scanning Trending Stocks"):
        raw_symbols = get_trending_symbols()
        skipped = load_skipped_symbols()
        allowed_symbols = [s for s in raw_symbols if s not in skipped]
        allowed_symbols = filter_cooldown_symbols(allowed_symbols)

        st.session_state["symbol_batches"] = [allowed_symbols[i:i+10] for i in range(0, len(allowed_symbols), 10)]
        st.session_state["current_batch"] = 0

if "symbol_batches" in st.session_state and st.session_state.get("current_batch", 0) < len(st.session_state["symbol_batches"]):
    batch = st.session_state["symbol_batches"][st.session_state["current_batch"]]
    st.subheader(f"📊 Scanning batch {st.session_state['current_batch'] + 1} of {len(st.session_state['symbol_batches'])}")

    for symbol in batch:
        st.markdown(f"### 🔍 {symbol}")
        data = fetch_historical_data(symbol, start_date, end_date)
        if data is None or data.empty:
            st.warning("⚠️ No data available.")
            continue

        golden_crosses, _ = detect_crossovers(data)

        # ✅ Filter to recent crosses if checkbox is checked
        if show_recent_only:
            cutoff = datetime.today() - timedelta(days=30)
            golden_crosses = [date for date in golden_crosses if date >= cutoff]

        if golden_crosses and isinstance(golden_crosses[-1], pd.Timestamp):
            last_cross = golden_crosses[-1]
            st.success(f"✨ Golden Cross on {last_cross.strftime('%Y-%m-%d')}")
            fig = plot_stock_data_with_indicators(data, symbol, [last_cross], [])
            st.pyplot(fig)
        elif golden_crosses:
            st.warning(f"⚠️ Found {len(golden_crosses)} crosses, but data is not in the expected format: {golden_crosses}")

        elif golden_crosses:
            st.warning(f"⚠️ Found {len(golden_crosses)} crosses, but data is not in the expected format: {golden_crosses}")
else:
    st.info("📉 No recent golden cross.")

if st.button("Next Batch"):
    if "current_batch" not in st.session_state:
        st.session_state["current_batch"] = 0
    if st.session_state["current_batch"] < len(st.session_state["symbol_batches"]) - 1:
        st.session_state["current_batch"] += 1
        st.rerun()
    else:
        st.warning("✅ All batches have been scanned.")

