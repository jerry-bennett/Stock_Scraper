import requests
from bs4 import BeautifulSoup
import time
import random

def load_stock_symbols():
    urls = {
        "Most Active": "https://finance.yahoo.com/most-active",
        "Trending": "https://finance.yahoo.com/trending-tickers",
        "Gainers": "https://finance.yahoo.com/gainers",
        "Losers": "https://finance.yahoo.com/losers",
    }

    stock_symbols = set()

    for category, url in urls.items():
        try:
            print(f"\nFetching stock symbols for: {category} ({url})...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise error for HTTP issues

            soup = BeautifulSoup(response.text, "html.parser")
            table_rows = soup.select("table tbody tr")

            symbols = []
            for row in table_rows:
                columns = row.find_all("td")
                if columns:
                    symbol = columns[0].text.strip()
                    stock_symbols.add(symbol)
                    symbols.append(symbol)

            print(f"Fetched {len(symbols)} symbols: {symbols}")

            # Delay between requests to prevent getting blocked
            # time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"Error fetching data from {url}: {e}")

    

    final_symbols = list(stock_symbols)
    print(f"\nTotal unique stock symbols collected: {len(final_symbols)}\n{final_symbols}")  # Final summary
    return final_symbols
