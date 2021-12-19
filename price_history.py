from datetime import date, datetime, timedelta
from fetch_price_history import PriceHistoryFetcher
from watchlist import watchlist
import numpy

class PriceHistory:
    def __init__(self) -> None:
        phf = PriceHistoryFetcher(watchlist)
        self.prices = phf.fetch_incremental()

    def price(self, date, symbol):
        retries = 0
        while date not in self.prices.index or numpy.isnan(self.prices.loc[date, symbol]):
            date = date - timedelta(days=1)
            retries += 1
            if retries == 6:
                print(f"Don't have data for {symbol} in the last 6 days from {date}")
                return 0
        return self.prices.loc[date, symbol]


if __name__ == "__main__":
    p = PriceHistory()
    print(p.price(datetime.fromisoformat('2019-01-27'), 'AAPL'))