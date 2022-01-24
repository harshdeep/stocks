from datetime import date, datetime, timedelta
from fetch_price_history import PriceHistoryFetcher
from starting_positions import Position
from watchlist import Watchlist
import numpy as np

class PriceHistory:
    def __init__(self) -> None:
        phf = PriceHistoryFetcher(Watchlist.load())
        self.prices = phf.fetch_stored()

    def price(self, date: date, symbol):
        retries = 0
        while date not in self.prices.index:
            date = date - timedelta(days=1)
            retries += 1
            if retries == 6:
                print(f"Don't have data for {symbol} in the last 6 days from {date}")
                return 0
        return self.prices.loc[date, symbol]

    def positionValue(self, date: date, position: Position):
        if position.quantity == 0:
            return 0
        price = self.price(date, position.symbol)
        if price == 0:
            return position.costBasis
        return position.quantity * price

    def priceHistory(self, symbol: str, start_date: date, end_date: date):
        df = self.prices.loc[start_date:end_date, symbol]
        last_value = df[-1]
        date = df.index[-1]
        while date < end_date:
            date += timedelta(days=1)
            df[date] = last_value
        return df.values.tolist()

    def movingAverage(self, symbol: str, window: int):
        window = int((7 * window)/5) # since we fill in days with no values, which is mainly weekends. not perfect but ok for the job
        return np.mean(self.prices.tail(window)[symbol])

if __name__ == "__main__":
    p = PriceHistory()
    print(p.price(datetime.fromisoformat('2019-01-27').date(), 'AAPL'))