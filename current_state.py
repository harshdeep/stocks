from datetime import datetime, timedelta
from price_history import PriceHistory
from starting_positions import StartingPositions
from trades import Trades
import csv
from utils import Utils

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

        today = datetime.today()
        today = datetime(year=today.year, month=today.month, day=today.day)

        with open('current_state.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'quantity', 'cost_basis', 'current_value'])

            gain = 0
            non_fb_gain = 0
            for symbol, value in currentPositions.items():
                current_value = value['quantity'] * priceHistory.price(today, symbol)
                writer.writerow({
                    'symbol': symbol,
                    'quantity': value['quantity'],
                    'cost_basis': value['cost_basis'],
                    'current_value': value['quantity'] * priceHistory.price(today, symbol)
                })
                gain = gain + (current_value - value['cost_basis'])
                if symbol != 'FB':
                    non_fb_gain += (current_value - value['cost_basis'])
            Utils.print_currency('Overall gain', gain)
            Utils.print_currency('Non-FB gain', non_fb_gain)

if __name__ == "__main__":
    CurrentState().compute()