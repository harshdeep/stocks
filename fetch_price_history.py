from datetime import date, timedelta, datetime
from pandas.core.frame import DataFrame
import yfinance as yf
from watchlist import Watchlist
import pandas as pd
import numpy as numpy
import argparse
from utils import Utils

class PriceHistoryFetcher:
    FILE_NAME = "data/prices.csv"
    def __init__(self, symbols) -> None:
        self.symbols = symbols
        self.symbolStr = " ".join(symbols)

    def download(self, start_date):
        return yf.download(self.symbolStr, start=start_date)["Close"]

    def store(self, data: DataFrame) -> None:
        data.sort_index()
        data.index = [d.date() for d in data.index]
        data.index.name = "Date"
        data.ffill(inplace=True)
        data.bfill(inplace=True)
        data.to_csv(self.FILE_NAME)

    def fetch_stored(self) -> DataFrame:
        stored = pd.read_csv(self.FILE_NAME, index_col='Date')
        stored.index = pd.to_datetime(stored.index)
        stored.index = [d.date() for d in stored.index]
        stored.index.name = "Date"
        return stored

    def fetch_fresh(self):
        Utils.log("Start download")
        data = self.download("2019-01-01")
        Utils.log("Store locally")
        self.store(data)
        return self.fetch_stored()

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
        last_date_with_data = self.last_date_with_data(stored)
        if last_date_with_data >= date.today():
            Utils.log("Not updating because we have today's data")
            return stored

        # else fetch the delta
        start_date = last_date_with_data + timedelta(days = 1)
        downloaded = self.download(start_date)

        # insert delta
        updated_rows = stored[stored.index.isin(downloaded.index)]
        Utils.log("Dropping {0} rows".format(updated_rows.shape[0]))

        stored.drop(updated_rows.index, inplace=True)

        Utils.log("Appending {0} rows".format(downloaded.shape[0]))
        updated = stored.append(downloaded)

        # store updated data
        self.store(updated)
        return self.fetch_stored()

def main():
    Utils.log('Started fetch_price_history')
    parser = argparse.ArgumentParser()
    parser.add_argument('method', choices=['fresh', 'incremental'])
    args = parser.parse_args()

    phf = PriceHistoryFetcher(Watchlist.load())

    Utils.log(f'method = {args.method}')
    if args.method == 'incremental':
        phf.fetch_incremental()
    else:
        phf.fetch_fresh()

    Utils.log("Finished fetch_price_history")

if __name__ == "__main__":
    main()
    #phf = PriceHistoryFetcher(Watchlist.load())
    #print(phf.fetch_incremental())