import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from update_stocks import load_stock_symbols  # Import the function that scrapes the stock symbols

def fetch_historical_data(stock_symbol, start_date, end_date):
    # Fetch historical data using yfinance
    stock = yf.Ticker(stock_symbol)
    historical_data = stock.history(period='1d', start=start_date, end=end_date)
    return historical_data

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
    for stock_symbol in stock_symbols:
        print(f"Checking {stock_symbol}...")
        historical_data = fetch_historical_data(stock_symbol, start_date, end_date)
        
        if not historical_data.empty:
            golden_cross, death_cross = detect_crossovers(historical_data)
            
            if golden_cross:
                print(f"\nGolden Cross (Buy) occurred for {stock_symbol} on: {golden_cross}")
                plot_stock_data_with_indicators(historical_data, stock_symbol, golden_cross, [])  # Pass the crossovers
                
            elif death_cross:
                print(f"\nDeath Cross (Sell) occurred for {stock_symbol} on: {death_cross}")
                plot_stock_data_with_indicators(historical_data, stock_symbol, [], death_cross)  # Pass the crossovers
                
        else:
            print(f"No historical data found for {stock_symbol}.")
    
    print("\nFinished checking all stocks.")

def main():
    # Prompt user for mode selection
    print("Would you like to:")
    print("1. Check current trending stocks")
    print("2. Check one specific stock")
    choice = input("Enter 1 or 2: ").strip()

    # Load stock symbols dynamically for trending stocks
    if choice == "1":
        stock_symbols = load_stock_symbols()
        print(f"Loaded {len(stock_symbols)} trending stocks.")
    elif choice == "2":
        specific_stock = input("Enter the stock symbol (e.g., AAPL, TSLA): ").strip().upper()
        stock_symbols = [specific_stock]  # Use a single stock symbol in the list
    else:
        print("Invalid choice. Please restart the program and choose either 1 or 2.")
        return

    # Get date range
    start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter the end date (YYYY-MM-DD): ").strip()

    # Check for crossovers
    check_stocks_for_crossovers(stock_symbols, start_date, end_date)

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
