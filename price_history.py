from datetime import date, datetime, timedelta
from fetch_price_history import PriceHistoryFetcher
from starting_positions import Position
from watchlist import Watchlist
import numpy

class PriceHistory:
    def __init__(self) -> None:
        phf = PriceHistoryFetcher(Watchlist.load())
        #self.prices = phf.fetch_incremental()
        self.prices = phf.fetch_stored()

    def price(self, date, symbol):
        retries = 0
        while date not in self.prices.index or numpy.isnan(self.prices.loc[date, symbol]):
            date = date - timedelta(days=1)
            retries += 1
            if retries == 6:
                #print(f"Don't have data for {symbol} in the last 6 days from {date}")
                return 0
        return self.prices.loc[date, symbol]

    def positionValue(self, date: datetime, position: Position):
        if position.quantity == 0:
            return 0
        price = self.price(date, position.symbol)
        if price == 0:
            return position.costBasis
        return position.quantity * price

    def priceHistory(self, symbol: str, start_date: datetime, end_date: datetime):
        df = self.prices.loc[start_date:end_date, symbol].ffill()
        last_value = df[-1]
        date = df.index[-1]
        while date < end_date:
            date += timedelta(days=1)
            df[date] = last_value
        return df.values.tolist()

if __name__ == "__main__":
    p = PriceHistory()
    print(p.price(datetime.fromisoformat('2019-01-27'), 'AAPL'))