import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time
import json
import os
from datetime import datetime, timedelta
from update_stocks import load_stock_symbols  # Import the function that scrapes the stock symbols
import random

def fetch_historical_data(symbol, start, end):
    df = yf.download(symbol, start=start, end=end)
    
    if df is not None and not df.empty:
        if len(df) >= 200:
            df['50_MA'] = df['Close'].rolling(window=50).mean()
            df['200_MA'] = df['Close'].rolling(window=200).mean()
        else:
            print(f"⚠️ Not enough data for 50/200 MA for {symbol} ({len(df)} rows)")
        return df

    return None

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

def detect_crossovers(df, short=50, long=200):
    df = df.copy()
    df["SMA_short"] = df["Close"].rolling(window=short).mean()
    df["SMA_long"] = df["Close"].rolling(window=long).mean()
    df.dropna(inplace=True)

    if df.empty:
        return [], []

    golden_crosses = []
    death_crosses = []
    prev_short = df["SMA_short"].iloc[0]
    prev_long = df["SMA_long"].iloc[0]

    for i in range(1, len(df)):
        curr_short = df["SMA_short"].iloc[i]
        curr_long = df["SMA_long"].iloc[i]
        date = df.index[i]

        if prev_short < prev_long and curr_short >= curr_long:
            golden_crosses.append(date)
        elif prev_short > prev_long and curr_short <= curr_long:
            death_crosses.append(date)

        prev_short = curr_short
        prev_long = curr_long

    return golden_crosses, death_crosses

def check_stocks_for_crossovers(stock_symbols, start_date, end_date, recent_only=False, recent_days=30):
    valid_symbols = []
    skipped_symbols = load_skipped_symbols()
    updated_skipped = skipped_symbols.copy()
    today = datetime.today()
    recent_cutoff = today - timedelta(days=recent_days)

    for stock_symbol in stock_symbols:
        if stock_symbol in skipped_symbols:
            print(f"⏩ Skipping {stock_symbol} (recently checked)")
            continue

        print(f"\n🔍 Checking {stock_symbol}...")

        historical_data = fetch_historical_data(stock_symbol, start_date, end_date)
        if historical_data is not None:
            golden_crosses, death_crosses = detect_crossovers(historical_data)

            if recent_only:
                golden_crosses = [date for date in golden_crosses if date >= recent_cutoff]
                death_crosses = [date for date in death_crosses if date >= recent_cutoff]

            if golden_crosses:
                print(f"\n📈 {stock_symbol}: Golden Cross on {golden_crosses[-1].strftime('%Y-%m-%d')}")
                plot_stock_data_with_indicators(historical_data, stock_symbol, [golden_crosses[-1]], [])

            else:
                print(f"📉 No significant crossover found for {stock_symbol}.")


            valid_symbols.append(stock_symbol)
        else:
            print(f"❌ Skipping {stock_symbol} due to missing or invalid data.")
            updated_skipped[stock_symbol] = today.strftime("%Y-%m-%d")

        time.sleep(1.5)

    save_skipped_symbols(updated_skipped)
    print(f"\n✅ Finished checking stocks. {len(valid_symbols)} had valid data.")

SKIPPED_FILE = "skipped_symbols.json"
SKIP_DAYS = 3  # Number of days to temporarily skip symbols

TRENDING_CACHE_FILE = "trending_cache.json"
TRENDING_CACHE_DAYS = 3  # days before refresh


from datetime import datetime, timedelta

def is_date_recent(date_str, days=1):
    """Return True if the date string is within the last `days` days."""
    try:
        skipped_date = datetime.strptime(date_str, "%Y-%m-%d")
        return datetime.now() - skipped_date < timedelta(days=days)
    except ValueError:
        return False

def load_skipped_symbols():
    file_path = 'skipped_stocks.json'
    if not os.path.exists(file_path):
        return {}

    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return {
                    symbol: date_str for symbol, date_str in data.items()
                    if not is_date_recent(date_str)
                }
            else:
                return {}
        except json.JSONDecodeError:
            return {}


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
def reset_cached_data():
    # Customize these paths if your JSON files are stored elsewhere
    cache_files = ['trending_cache.json', 'skipped_symbols.json']
    
    for file in cache_files:
        try:
            with open(file, 'w') as f:
                json.dump({}, f)
            print(f"✅ Reset {file}")
        except Exception as e:
            print(f"❌ Failed to reset {file}: {e}")

#logic for 'cooldown' stocks. for day trading.
COOLDOWN_FILE = "cooldown.json"

def load_cooldown():
    """
    Return {symbol: datetime} for every symbol still in the cooldown file.
    Accepts both 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM:SS' strings.
    """
    if not os.path.exists(COOLDOWN_FILE):
        return {}

    # Read the raw JSON
    try:
        with open(COOLDOWN_FILE, "r") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

    # Parse with either format
    parsed = {}
    for symbol, date_str in raw.items():
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed[symbol] = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue  # try the next format

    return parsed


def save_cooldown(cooldown_dict):
    with open(COOLDOWN_FILE, "w") as f:
        data = {
            symbol: date.strftime("%Y-%m-%d %H:%M:%S")
            for symbol, date in cooldown_dict.items()
        }
        json.dump(data, f, indent=2)

def update_cooldown(symbol):
    cooldown = load_cooldown()
    cooldown[symbol] = datetime.now()
    save_cooldown(cooldown)

def is_in_cooldown(symbol, cooldown_period_hours=24):
    cooldown = load_cooldown()
    if symbol not in cooldown:
        return False
    last_sold = cooldown[symbol]
    return datetime.now() - last_sold < timedelta(hours=cooldown_period_hours)

def filter_cooldown_symbols(symbols):
    return [s for s in symbols if not is_in_cooldown(s)]

def add_to_cooldown(symbols, days=2):
    try:
        with open(COOLDOWN_FILE, "r") as f:
            cooldown_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cooldown_data = {}

    expiry_date = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    for symbol in symbols:
        cooldown_data[symbol] = expiry_date

    with open(COOLDOWN_FILE, "w") as f:
        json.dump(cooldown_data, f, indent=2)

    print(f"✅ Added {len(symbols)} symbols to cooldown until {expiry_date}")

MAX_STOCKS = 10      
SKIP_DAYS   = 3         

def main():
    # Prompt user for mode selection
    print("Would you like to:")
    print("1. Check current trending stocks")
    print("2. Check one specific stock")
    print("3. Reset cached data")
    print("4. Add symbols to cooldown")
    choice = input("Enter 1, 2, 3, or 4 ").strip()

    if choice == "1":
        show_recent_only = None
        while show_recent_only not in ('y', 'n'):
            show_recent_only = input("Show only recent crosses? (y/n): ").strip().lower()
        show_recent_only = (show_recent_only == 'y')
        raw_symbols = get_trending_symbols()
        skipped_dict = load_skipped_symbols()

        # Exclude skipped
        today_allowed = [s for s in raw_symbols if s not in skipped_dict]
        today_allowed = filter_cooldown_symbols(today_allowed)

        # Shuffle before slicing
        random.shuffle(today_allowed)
        max_stocks = 10
        stock_symbols = today_allowed
        print(f"Loaded {len(stock_symbols)} trending stocks (limited to {max_stocks}).")

    elif choice == "2":
        show_recent_only = None
        while show_recent_only not in ('y', 'n'):
            show_recent_only = input("Show only recent crosses? (y/n): ").strip().lower()
        show_recent_only = (show_recent_only == 'y')
        raw_symbols = get_trending_symbols()
        skipped_dict = load_skipped_symbols()
        specific_stock = input("Enter the stock symbol (e.g., AAPL, TSLA): ").strip().upper()
        stock_symbols = [specific_stock]

    elif choice == "3":
        reset_cached_data()
        return
    
    elif choice == "4":
        user_input = input("Enter the symbols sold today (comma-separated): ")
        sold_today = [s.strip().upper() for s in user_input.split(",") if s.strip()]
        days = input("How many days to cooldown? (default is 2): ").strip()
        days = int(days) if days.isdigit() else 2
        add_to_cooldown(sold_today, days)
        return

    else:
        print("Invalid choice. Please restart the program and choose either 1, 2, 3 or 4.")
        return

    # Get date range
    start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter the end date (YYYY-MM-DD): ").strip()

    # Process in batches of MAX_STOCKS (10)
    total = len(stock_symbols)
    for i in range(0, total, MAX_STOCKS):
        batch = stock_symbols[i:i+MAX_STOCKS]
        check_stocks_for_crossovers(batch, start_date, end_date, recent_only=show_recent_only)

        if i + MAX_STOCKS >= total:
            print("\n✅ Finished processing all stocks.")
            break

        cont = input("\nContinue with next batch? (y/n): ").strip().lower()
        if cont != 'y':
            print("Stopping early as requested.")
            break

    # Check for crossovers
    #check_stocks_for_crossovers(stock_symbols, start_date, end_date, recent_only=show_recent_only)

if __name__ == "__main__":
    main()
