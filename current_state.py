from datetime import datetime, timedelta
from price_history import PriceHistory
from starting_positions import StartingPositions
from trades import Trades
import csv
from utils import Utils
import pandas as pd

class CurrentState:
    def __init__(self) -> None:
        self.startingPositions = StartingPositions()
        self.startingPositions.load()

        self.trades = Trades()
        self.trades.load()

        self.priceHistory = PriceHistory()

    def applyTrade(self, trade, positions):
        symbol = trade['symbol']

        if symbol not in positions:
            positions[symbol] = {'quantity': 0, 'cost_basis': 0}

        quantity = trade['quantity']
        cost_basis = trade['quantity'] * trade['price']

        if trade['action'] == 'Buy' or trade['action'] == 'RSU':
            positions[symbol]['quantity'] += quantity
            positions[symbol]['cost_basis'] += cost_basis
        elif trade['action'] == 'Sell':
            if quantity > positions[symbol]['quantity']:
                print(f"Sold {quantity} {symbol} shares but held only {positions[symbol]['quantity']}")
                quantity = positions[symbol]['quantity']
            positions[symbol]['quantity'] -= quantity
            positions[symbol]['cost_basis'] -= cost_basis

    def computeOverall(self):
        currentPositions = self.startingPositions.positions.copy()

        for trade in self.trades.trades:
            self.applyTrade(trade, currentPositions)

        today = Utils.today()

        result = []
        total_gain = 0
        total_non_fb_gain = 0

        for symbol, position in currentPositions.items():
            current_price = self.priceHistory.price(today, symbol)
            current_value = position['quantity'] * current_price
            gain = current_value - position['cost_basis']
            result.append({
                'symbol': symbol,
                'quantity': position['quantity'],
                'cost_basis': position['cost_basis'],
                'current_value': current_value,
                'gain': gain,
                'cost_basis_per_share': position['cost_basis'] / position['quantity'] if position['quantity'] != 0 else 0,
                'current_price_per_share': current_price,
            })
            total_gain += gain
            if symbol != 'FB':
                total_non_fb_gain += gain

        Utils.writeCSV('current_state.csv', result)
        Utils.print_currency('Overall gain', total_gain)
        Utils.print_currency('Non-FB gain', total_non_fb_gain)

    def computeTimeSeries(self, start_date, end_date):
        current_positions = self.startingPositions.positions.copy()
        date = self.trades.trades[0]['date']
        assert(date < start_date)
        assert(start_date < end_date)

        day = timedelta(days=1)

        # Run up to the start date
        while date < start_date:
            for trade in [t for t in self.trades.trades if t['date'] == date]:
                self.applyTrade(trade, current_positions)
            date += day

        # Reset cost basis on start date
        for symbol, position in current_positions.items():
            if position['quantity'] == 0:
                position['cost_basis'] = 0
            else:
                position['cost_basis'] = position['quantity'] * self.priceHistory.price(start_date, symbol)

        result = []
        cumulative_deposit = 0
        cumulative_withdrawn = 0

        while date <= end_date:
            # apply trades from this day
            deposit = 0
            withdrawn = 0

            for trade in [t for t in self.trades.trades if t['date'] == date]:
                self.applyTrade(trade, current_positions)

                trade_value = trade['quantity'] * trade['price']
                if trade['action'] == 'Buy':
                    deposit += trade_value
                elif trade['action'] == 'Sell' and trade['symbol'] != 'FB':
                    withdrawn += trade_value

            cumulative_deposit += deposit
            cumulative_withdrawn += withdrawn

            value = 0
            gain = 0
            non_fb_value = 0
            non_fb_gain = 0
            for symbol, position in current_positions.items():
                if position['quantity'] == 0:
                    current_value = 0
                else:
                    current_value = position['quantity'] * self.priceHistory.price(date, symbol)
                current_gain = current_value - position['cost_basis']
                value += current_value
                gain += current_gain
                if symbol != 'FB':
                    non_fb_value += current_value
                    non_fb_gain += current_gain

            result.append({
                'date': date,
                'value': value,
                'gain': gain,
                'non_fb_value': non_fb_value,
                'non_fb_gain': non_fb_gain,
                'deposit': deposit,
                'withdrawn': withdrawn,
                'net_non_fb_value': non_fb_value - cumulative_deposit + cumulative_withdrawn
            })
            date += day

        Utils.writeCSV('timeseries.csv', result)

if __name__ == "__main__":
    CurrentState().computeOverall()
    #CurrentState().computeTimeSeries(datetime.fromisoformat('2021-01-01'), Utils.today())