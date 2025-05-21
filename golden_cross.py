import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
import yfinance as yf
import json
import os
from datetime import datetime, timedelta
from update_stocks import load_stock_symbols  # Import the function that scrapes the stock symbols
import random

import yfinance as yf
1
def fetch_historical_data(stock_symbol, start_date, end_date):
    try:
        stock = yf.Ticker(stock_symbol)
        historical_data = stock.history(period='1d', start=start_date, end=end_date)

        if historical_data.empty:
            print(f"⚠️ No historical data found for {stock_symbol}. It might be delisted or invalid.")
            return None  # Return None for invalid symbols

        return historical_data

    except Exception as e:
        print(f"❌ Failed to fetch data for {stock_symbol}: {e}")
        return None  # Return None on failure


def calculate_indicators(historical_data):
    # Calculate RSI
    delta = historical_data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    historical_data['RSI'] = 100 - (100 / (1 + rs))

    # Calculate MACD
    ema_12 = historical_data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = historical_data['Close'].ewm(span=26, adjust=False).mean()
    historical_data['MACD'] = ema_12 - ema_26
    historical_data['Signal_Line'] = historical_data['MACD'].ewm(span=9, adjust=False).mean()

    # Calculate Bollinger Bands
    rolling_mean = historical_data['Close'].rolling(window=20).mean()
    rolling_std = historical_data['Close'].rolling(window=20).std()
    historical_data['Upper_Band'] = rolling_mean + (rolling_std * 2)
    historical_data['Lower_Band'] = rolling_mean - (rolling_std * 2)
    
    return historical_data

def plot_stock_data_with_indicators(historical_data, stock_symbol, golden_cross, death_cross):
    historical_data = calculate_indicators(historical_data)

    # Create the main plot for price and moving averages
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), gridspec_kw={'height_ratios': [2, 1, 1]})
    fig.suptitle(f'{stock_symbol} Stock Analysis', fontsize=16)

    # Plot closing price and moving averages
    ax1.plot(historical_data.index, historical_data['Close'], label='Closing Price', color='blue', linewidth=1)
    ax1.plot(historical_data.index, historical_data['50_MA'], label='50-Day MA', color='orange', linestyle='--')
    ax1.plot(historical_data.index, historical_data['200_MA'], label='200-Day MA', color='green', linestyle='--')

    # Plot golden and death crosses
    for date in golden_cross:
        ax1.scatter(date, historical_data.loc[date]['Close'], color='green', label="Golden Cross", zorder=5)
    for date in death_cross:
        ax1.scatter(date, historical_data.loc[date]['Close'], color='red', label="Death Cross", zorder=5)

    ax1.set_title('Price and Moving Averages')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price (USD)')
    ax1.legend()
    ax1.grid(True)

    # Plot RSI
    ax2.plot(historical_data.index, historical_data['RSI'], label='RSI', color='purple', linewidth=1)
    ax2.axhline(70, color='red', linestyle='--', linewidth=0.8, label='Overbought')
    ax2.axhline(30, color='green', linestyle='--', linewidth=0.8, label='Oversold')
    ax2.set_title('Relative Strength Index (RSI)')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('RSI Value')
    ax2.legend()
    ax2.grid(True)

    # Plot MACD
    ax3.plot(historical_data.index, historical_data['MACD'], label='MACD', color='blue', linewidth=1)
    ax3.plot(historical_data.index, historical_data['Signal_Line'], label='Signal Line', color='red', linewidth=0.8)
    ax3.bar(historical_data.index, historical_data['MACD'] - historical_data['Signal_Line'], label='Histogram', color='gray', alpha=0.5)
    ax3.set_title('MACD (Moving Average Convergence Divergence)')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('MACD Value')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

def detect_crossovers(historical_data):
    # Calculate the moving averages again in case the data has changed or is missing
    historical_data['50_MA'] = historical_data['Close'].rolling(window=50).mean()
    historical_data['200_MA'] = historical_data['Close'].rolling(window=200).mean()

    # Drop rows with NaN values in the moving averages columns
    historical_data = historical_data.dropna(subset=['50_MA', '200_MA'])

    # Golden Cross and Death Cross detection
    golden_cross = []
    death_cross = []
    
    for i in range(1, len(historical_data)):
        # Use .iloc[] for index-based access
        if historical_data.iloc[i]['50_MA'] > historical_data.iloc[i]['200_MA'] and historical_data.iloc[i-1]['50_MA'] <= historical_data.iloc[i-1]['200_MA']:
            golden_cross.append(historical_data.index[i])
        elif historical_data.iloc[i]['50_MA'] < historical_data.iloc[i]['200_MA'] and historical_data.iloc[i-1]['50_MA'] >= historical_data.iloc[i-1]['200_MA']:
            death_cross.append(historical_data.index[i])
    
    return golden_cross, death_cross

def check_stocks_for_crossovers(stock_symbols, start_date, end_date):
    valid_symbols = []
    skipped_symbols = load_skipped_symbols()
    updated_skipped = skipped_symbols.copy()
    today_str = datetime.today().strftime("%Y-%m-%d")

    for stock_symbol in stock_symbols:
        if stock_symbol in skipped_symbols:
            print(f"⏩ Skipping {stock_symbol} (recently checked)")
            continue

        print(f"\n🔍 Checking {stock_symbol}...")

        historical_data = fetch_historical_data(stock_symbol, start_date, end_date)

        if historical_data is not None:
            golden_cross, death_cross = detect_crossovers(historical_data)

            if golden_cross:
                print(f"\n✨ Golden Cross (Buy Signal) detected for {stock_symbol} on: {golden_cross}")
                plot_stock_data_with_indicators(historical_data, stock_symbol, golden_cross, [])
            elif death_cross:
                print(f"\n⚠️ Death Cross (Sell Signal) detected for {stock_symbol} on: {death_cross}")
                plot_stock_data_with_indicators(historical_data, stock_symbol, [], death_cross)
            else:
                print(f"📉 No significant crossover found for {stock_symbol}.")
                updated_skipped[stock_symbol] = today_str  # Track as temporarily uninteresting

            valid_symbols.append(stock_symbol)

        else:
            print(f"❌ Skipping {stock_symbol} due to missing or invalid data.")
            updated_skipped[stock_symbol] = today_str

        time.sleep(1.5)  # Prevent rate limiting

    save_skipped_symbols(updated_skipped)
    print(f"\n✅ Finished checking stocks. {len(valid_symbols)} had valid data.")

SKIPPED_FILE = "skipped_symbols.json"
SKIP_DAYS = 3  # Number of days to temporarily skip symbols

TRENDING_CACHE_FILE = "trending_cache.json"
TRENDING_CACHE_DAYS = 3  # days before refresh

def load_skipped_symbols():
    if not os.path.exists(SKIPPED_FILE):
        return {}

    with open(SKIPPED_FILE, "r") as f:
        data = json.load(f)

    # Filter out expired skip entries
    today = datetime.today().date()
    return {
        symbol: date_str for symbol, date_str in data.items()
        if (today - datetime.strptime(date_str, "%Y-%m-%d").date()).days < SKIP_DAYS
    }

def save_skipped_symbols(skipped):
    with open(SKIPPED_FILE, "w") as f:
        json.dump(skipped, f)

def load_cached_trending():
    if not os.path.exists(TRENDING_CACHE_FILE):
        return None

    with open(TRENDING_CACHE_FILE, "r") as f:
        try:
            data = json.load(f)
            timestamp = data.get("timestamp", 0)
            age_days = (time.time() - timestamp) / (60 * 60 * 24)

            if age_days > TRENDING_CACHE_DAYS:
                return None  # Too old, need to refresh
            return data.get("symbols", [])
        except Exception as e:
            print(f"Failed to load trending cache: {e}")
            return None
        
def save_cached_trending(symbols):
    with open(TRENDING_CACHE_FILE, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "symbols": symbols
        }, f)
def get_trending_symbols():
        cached = load_cached_trending()
        if cached:
            print("✅ Using cached trending stocks.")
            return cached

        print("🔄 Fetching fresh trending stocks...")
        symbols = load_stock_symbols()
        save_cached_trending(symbols)
        return symbols

MAX_STOCKS = 10      
SKIP_DAYS   = 3         

def main():
    # Prompt user for mode selection
    print("Would you like to:")
    print("1. Check current trending stocks")
    print("2. Check one specific stock")
    choice = input("Enter 1 or 2: ").strip()

    # Load stock symbols dynamically for trending stocks
    if choice == "1":
        stock_symbols = get_trending_symbols()
        max_stocks = 10  
        stock_symbols = stock_symbols[:max_stocks]
        print(f"Loaded {len(stock_symbols)} trending stocks (limited to {max_stocks}).")
    elif choice == "2":
        specific_stock = input("Enter the stock symbol (e.g., AAPL, TSLA): ").strip().upper()
        stock_symbols = [specific_stock]  # Use a single stock symbol in the list
    else:
        print("Invalid choice. Please restart the program and choose either 1 or 2.")
        return
    
    # Load trending and skip list
    raw_symbols  = get_trending_symbols()
    skipped_dict = load_skipped_symbols()

    # Exclude skipped
    today_allowed = [s for s in raw_symbols if s not in skipped_dict]

    # Shuffle before slicing
    random.shuffle(today_allowed)
    stock_symbols = today_allowed[:MAX_STOCKS]

    # Get date range
    start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter the end date (YYYY-MM-DD): ").strip()

    # Check for crossovers
    check_stocks_for_crossovers(stock_symbols, start_date, end_date)

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
