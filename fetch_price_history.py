from datetime import date, timedelta, datetime
from pandas.core.frame import DataFrame
import yfinance as yf
from watchlist import Watchlist
import pandas as pd
import numpy as numpy
import argparse

class PriceHistoryFetcher:
    FILE_NAME = "prices.csv"
    def __init__(self, symbols) -> None:
        self.symbols = symbols
        self.symbolStr = " ".join(symbols)

    def download(self, start_date):
        return yf.download(self.symbolStr, start=start_date)["Adj Close"]

    def store(self, data: DataFrame) -> None:
        data.sort_index()
        data.to_csv(self.FILE_NAME)

    def fetch_stored(self) -> DataFrame:
        stored = pd.read_csv(self.FILE_NAME, index_col='Date')
        stored.index = pd.to_datetime(stored.index)
        return stored

    def fetch_fresh(self):
        data = self.download("2019-01-01")
        self.store(data)
        return data

    def last_date_with_data(self, data: DataFrame) -> date:
        vti = data.loc[:, ['VTI']]
        num_rows = vti.shape[0]
        index = num_rows - 1
        while index >= 0 and numpy.isnan(vti.iat[index, 0]):
            index -= 1
        return vti.index[index]

    def fetch_incremental(self):
        # fetch current data
        stored = self.fetch_stored()

        # if it's not outdated, just return it
        last_date_with_data = self.last_date_with_data(stored).date()
        if last_date_with_data >= date.today():
            print("Not updating because we have today's data")
            return stored

        # else fetch the delta
        start_date = last_date_with_data + timedelta(days = 1)
        downloaded = self.download(start_date)

        # insert delta
        updated_rows = stored[stored.index.isin(downloaded.index)]
        print("Dropping {0} rows".format(updated_rows.shape[0]))

        stored.drop(updated_rows.index, inplace=True)

        print("Appending {0} rows".format(downloaded.shape[0]))
        updated = stored.append(downloaded)

        # store updated data
        self.store(updated)
        return updated

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['fresh', 'incremental'])
    args = parser.parse_args()

    phf = PriceHistoryFetcher(Watchlist.load())

    if args.method == 'incremental':
        phf.fetch_incremental()
    else:
        phf.fetch_fresh()