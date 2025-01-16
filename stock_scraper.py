import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import os
print("Current Working Directory:", os.getcwd())

def fetch_stock_data(stock_symbol):
    """
    Fetch basic stock data from Yahoo Finance for the given stock symbol.
    """
    url = f"https://finance.yahoo.com/quote/{stock_symbol}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Debug: Save raw HTML for inspection
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())
    
    # Extract key stock data
    data = {}
    try:
        data['Stock'] = stock_symbol.upper()
        # Use the data-testid attribute to find the price
        price_element = soup.find('span', {'data-testid': 'qsp-price'})
        if price_element:
            data['Price'] = price_element.text
        else:
            raise ValueError("Price element not found.")
        
        data['Time Fetched'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error: {e}")
        return None

    return data

def main():
    print("Simple Stock Data Scraper\n")
    
    # Get user input
    stock_symbol = input("Enter the stock symbol (e.g., AAPL for Apple): ").strip()
    
    # Fetch stock data
    stock_data = fetch_stock_data(stock_symbol)
    if stock_data:
        # Display data in a table format
        df = pd.DataFrame([stock_data])
        print("\nStock Data:")
        print(df)
        
        # Save data to a CSV file
        df.to_csv(f'./{stock_symbol}_stock_data.csv', index=False)
        print(f"\nStock data saved to {stock_symbol}_stock_data.csv")
    else:
        print("Failed to fetch stock data. Please try again.")

if __name__ == "__main__":
    main()
