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
    reset_cached_data
)

st.set_page_config(page_title="Golden Cross Scanner", layout="centered")
st.title("📈 Golden Cross Stock Scanner")
st.markdown("_Scan for recent 50/200 SMA Golden Cross signals._")

# --- Mode Selection ---
mode = st.radio("Choose a mode:", ["🔎 Specific Stock", "🔥 Trending Stocks"])

# --- Shared Date Settings ---
with st.expander("⚙️ Scan Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(2024, 1, 1))
    with col2:
        end_date = st.date_input("End Date", datetime.today())

    show_recent_only = st.checkbox("Show only recent crosses (last 30 days)", value=True)

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# --- Mode 1: Specific Stock ---
if mode == "🔎 Specific Stock":
    symbol = st.text_input("Enter stock symbol", value="AAPL")
    if st.button("🔍 Check Symbol") and symbol:
        with st.spinner("Fetching and analyzing data..."):
            data = fetch_historical_data(symbol.upper(), start_str, end_str)
            if data is not None:
                golden_crosses, _ = detect_crossovers(data)
                if show_recent_only:
                    cutoff = datetime.today() - timedelta(days=30)
                    golden_crosses = [d for d in golden_crosses if d >= cutoff]

                if golden_crosses and isinstance(golden_crosses[-1], pd.Timestamp):
                    last_cross = golden_crosses[-1]
                    st.success(f"✨ Golden Cross detected on {last_cross.strftime('%Y-%m-%d')}")
                else:
                    st.info("📉 No recent golden cross found.")

                fig = plot_stock_data_with_indicators(data, symbol.upper(), golden_crosses)
                st.pyplot(fig)
            else:
                st.error("❌ Failed to fetch data for that symbol.")

# --- Mode 2: Trending Stocks ---
elif mode == "🔥 Trending Stocks":
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📈 Get Trending Symbols"):
            get_trending_symbols()
            st.success("Trending symbols updated.")

    with col2:
        if st.button("🧹 Reset Cache"):
            reset_cached_data()
            st.success("Trending cache and skipped symbols reset.")

    if st.button("▶️ Start Scanning Trending Stocks"):
        raw_symbols = get_trending_symbols()
        skipped = load_skipped_symbols()
        allowed_symbols = filter_cooldown_symbols([s for s in raw_symbols if s not in skipped])

        if allowed_symbols:
            st.session_state["symbol_batches"] = [allowed_symbols[i:i+10] for i in range(0, len(allowed_symbols), 10)]
            st.session_state["current_batch"] = 0
        else:
            st.warning("⚠️ No valid trending symbols to scan.")

    if st.button("⏭️ Next Batch"):
        if "current_batch" not in st.session_state:
            st.session_state["current_batch"] = 0
        elif st.session_state["current_batch"] < len(st.session_state["symbol_batches"]) - 1:
            st.session_state["current_batch"] += 1
            st.rerun()
        else:
            st.success("✅ All batches have been scanned.")

    # --- Display Current Batch ---
    if "symbol_batches" in st.session_state and st.session_state["current_batch"] < len(st.session_state["symbol_batches"]):
        batch = st.session_state["symbol_batches"][st.session_state["current_batch"]]
        st.markdown(f"##### 📊 Scanning Batch {st.session_state['current_batch'] + 1} of {len(st.session_state['symbol_batches'])}")

        with st.spinner("Analyzing symbols..."):
            cols = st.columns(2)  # Try 3 for smaller components

            for idx, symbol in enumerate(batch):
                with cols[idx % 2]:  # Cycle through the columns
                    st.markdown(f"### 🔍 {symbol}")
                    data = fetch_historical_data(symbol, start_str, end_str)
                    if data is None or data.empty:
                        st.info("📭 No data.")
                    else:
                        golden_crosses = detect_crossovers(data)
                        flat = []
                        for d in golden_crosses:
                            if isinstance(d, list):
                                flat.extend(d)
                            else:
                                flat.append(d)
                        golden_crosses = flat

                        if show_recent_only:
                            cutoff = datetime.today() - timedelta(days=30)
                            golden_crosses = [d for d in golden_crosses if d >= cutoff]
                        if show_recent_only:
                            cutoff = datetime.today() - timedelta(days=30)
                            golden_crosses = [d for d in golden_crosses if d >= cutoff]

                        if golden_crosses and isinstance(golden_crosses[-1], pd.Timestamp):
                            last_cross = golden_crosses[-1]
                            st.success(f"🌟 Golden Cross on {last_cross.strftime('%Y-%m-%d')}")
                            fig = plot_stock_data_with_indicators(data, symbol, [last_cross])
                            st.pyplot(fig)
                        else:
                            st.info("📉 No recent golden cross.")
    else:
        st.info("📉 No batch loaded or scanning not started.")
