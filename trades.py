import csv
from datetime import datetime

class Trades:
    FILE_NAME = 'trades.csv'

    def __init__(self) -> None:
        self.trades = []

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
                trade = {
                    'date': date,
                    'action': action,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                }
                self.trades.append(trade)
        self.trades.sort(key = lambda trade:trade['date'])

if __name__ == "__main__":
    t = Trades()
    t.load()
    print(t.trades)
    