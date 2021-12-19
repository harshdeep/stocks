from datetime import date, datetime
from fetch_price_history import PriceHistoryFetcher
from watchlist import watchlist

class PriceHistory:
    def __init__(self) -> None:
        phf = PriceHistoryFetcher(watchlist)
        self.prices = phf.fetch_incremental()
        #self.prices = phf.fetch_fresh()

    def price(self, date, symbol):
        return self.prices.loc[date, symbol]


if __name__ == "__main__":
    p = PriceHistory()
    print(p.price(datetime.fromisoformat('2021-12-13'), 'VTI'))