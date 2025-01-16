import requests
from bs4 import BeautifulSoup

def load_stock_symbols():
    # List of Yahoo Finance URLs to scrape
    urls = [
        "https://finance.yahoo.com/markets/stocks/most-active/",
        "https://finance.yahoo.com/markets/stocks/trending/",
        "https://finance.yahoo.com/markets/stocks/gainers/",
        "https://finance.yahoo.com/markets/stocks/losers/",
    ]

    stock_symbols = set()  # Use a set to avoid duplicate symbols

    for url in urls:
        try:
            print(f"Scraping stock symbols from: {url}")
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for HTTP issues
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find stock symbols in the table (adjust the selector as necessary)
            table_rows = soup.select("table tbody tr")
            for row in table_rows:
                columns = row.find_all("td")
                if len(columns) > 0:
                    symbol = columns[0].text.strip()  # Get the stock symbol
                    stock_symbols.add(symbol)  # Add to the set

        except Exception as e:
            print(f"Error while scraping {url}: {e}")

    return list(stock_symbols)  # Convert the set back to a list

if __name__ == "__main__":
    symbols = load_stock_symbols()
    print(f"Loaded stock symbols: {symbols}")
