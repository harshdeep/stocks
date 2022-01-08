import csv
from datetime import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class Trade:
    date: datetime
    action: str
    symbol: str
    quantity: float
    price: float
    account: str

class Trades:
    FILE_NAME = 'data/trades.csv'

    def __init__(self) -> None:
        self.trades: List[Trade] = []

    def load(self) -> List[Trade]:
        if self.trades:
            print("Trades data has already been loaded")
            return self.trades
        
        with open(self.FILE_NAME) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.trades.append(Trade(
                    datetime.strptime(row['Date'], "%m/%d/%y"),
                    row['Action'],
                    row['Symbol'],
                    float(row['Quantity']),
                    float(row['Price']),
                    row['Account']
                ))
        self.trades.sort(key = lambda trade:trade.date)
        return self.trades

if __name__ == "__main__":
    t = Trades()
    t.load()
    print(t.trades)
    