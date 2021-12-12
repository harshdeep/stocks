import yfinance as yf
from watchlist import watchlist

class PriceHistoryFetcher:
    def __init__(self) -> None:
        pass

    def fetch(self, symbols, start_date, end_date):
        pass

if __name__ == "__main__":
    msft = yf.Ticker("MSFT")
    print(watchlist)