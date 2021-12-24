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

class Trades:
    FILE_NAME = 'trades.csv'

    def __init__(self) -> None:
        self.trades: List[Trade] = []

    def load(self):
        if self.trades:
            print("Trades data has already been loaded")
            return
        
        with open(self.FILE_NAME) as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.strptime(row['Date'], "%m/%d/%y")
                action = row['Action']
                symbol = row['Symbol']
                quantity = float(row['Quantity'])
                price = float(row['Price'])
                # ignoring account for now
                trade = Trade(
                    date,
                    action,
                    symbol,
                    quantity,
                    price
                )
                self.trades.append(trade)
        self.trades.sort(key = lambda trade:trade.date)

if __name__ == "__main__":
    t = Trades()
    t.load()
    print(t.trades)
    