from datetime import datetime, timedelta
from price_history import PriceHistory
from starting_positions import StartingPositions
from trades import Trades
import csv

class CurrentState:
    def compute(self):
        startingPositions = StartingPositions()
        startingPositions.load()

        currentPositions = startingPositions.positions.copy()

        trades = Trades()
        trades.load()

        for trade in trades.trades:
            symbol = trade['symbol']

            if symbol not in currentPositions:
                currentPositions[symbol] = {'quantity': 0, 'cost_basis': 0}

            if trade['action'] == 'Buy' or trade['action'] == 'RSU':
                currentPositions[symbol]['quantity'] += trade['quantity']
                currentPositions[symbol]['cost_basis'] += trade['quantity'] * trade['price']
            elif trade['action'] == 'Sell':
                currentPositions[symbol]['quantity'] -= trade['quantity']
                currentPositions[symbol]['cost_basis'] -= trade['quantity'] * trade['price']

        priceHistory = PriceHistory()

        yesterday = datetime.today()
        yesterday = datetime(year = yesterday.year, month = yesterday.month, day = yesterday.day)# - timedelta(days = 1)
        print(yesterday)

        with open('current_state.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'quantity', 'cost_basis', 'current_value'])

            for symbol, value in currentPositions.items():
                writer.writerow({
                    'symbol': symbol,
                    'quantity': value['quantity'],
                    'cost_basis': value['cost_basis'],
                    'current_value': value['quantity'] * priceHistory.price(yesterday, symbol)
                })
            print("Done")

if __name__ == "__main__":
    CurrentState().compute()