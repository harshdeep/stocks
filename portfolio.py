from dataclasses import dataclass
from datetime import datetime, timedelta
from price_history import PriceHistory
from send_email import EmailSender
from starting_positions import Position, StartingPositions
from trades import Trade, Trades
from utils import Utils
from typing import List, Dict, Tuple

@dataclass
class AggregatePerfRow:
    date: datetime
    totalValue: float
    totalGain: float
    nonFBValue: float
    nonFBGain: float
    deposits: float
    withdrawals: float
    netNonFBValue: float

@dataclass
class FinalPosition:
    symbol: str
    startValue: float
    startQuantity: float
    value: float
    quantity: float
    gain: float
    bought: float
    sold: float
    gainOnCurrentValue: float
    gainOnStartValue: float

class Portfolio:
    def __init__(self) -> None:
        self.startingPositions = StartingPositions()
        self.startingPositions.load()

        self.trades = Trades()
        self.trades.load()

        self.priceHistory = PriceHistory()

    def applyTrade(self, trade: Trade, positions: Dict[str, Position]):
        symbol = trade.symbol

        if symbol not in positions:
            positions[symbol] = Position(symbol)

        quantity = trade.quantity
        cost_basis = trade.quantity * trade.price

        if trade.action == 'Buy' or trade.action == 'RSU':
            positions[symbol].quantity += quantity
            positions[symbol].costBasis += cost_basis
        elif trade.action == 'Sell':
            if quantity > positions[symbol].quantity:
                print(f"Sold {quantity} {symbol} shares but held only {positions[symbol].quantity}")
                quantity = positions[symbol].quantity
            positions[symbol].quantity -= quantity
            positions[symbol].costBasis -= cost_basis

    def state(self):
        currentPositions = self.startingPositions.positions.copy()

        for trade in self.trades.trades:
            self.applyTrade(trade, currentPositions)

        today = Utils.today()

        result = []
        total_gain = 0
        total_non_fb_gain = 0

        for position in currentPositions.values():
            current_price = self.priceHistory.price(today, position.symbol)
            current_value = position.quantity * current_price
            gain = current_value - position.costBasis
            result.append({
                'symbol': position.symbol,
                'quantity': position.quantity,
                'cost_basis': position.costBasis,
                'current_value': current_value,
                'gain': gain,
                'cost_basis_per_share': position.costBasisPerShare(),
                'current_price_per_share': current_price,
            })
            total_gain += gain
            if position.symbol != 'FB':
                total_non_fb_gain += gain

        Utils.writeCSV(f'artifacts/State {Utils.dateToStr(today)}.csv', result)
        Utils.print_currency('Overall gain', total_gain)
        Utils.print_currency('Non-FB gain', total_non_fb_gain)

        return result

    def timeSeries(self, start_date, end_date) -> Tuple[List[AggregatePerfRow], List[FinalPosition]]:
        current_positions = self.startingPositions.positions.copy()
        date = self.trades.trades[0].date
        assert(date < start_date)
        assert(start_date < end_date)

        day = timedelta(days=1)

        # Run up to the start date
        while date < start_date:
            for trade in [t for t in self.trades.trades if t.date == date]:
                self.applyTrade(trade, current_positions)
            date += day

        # Reset cost basis on start date
        for position in current_positions.values():
            position.costBasis = self.priceHistory.positionValue(start_date, position)
            position.resetStartValue()

        aggregate_perf = []
        cumulative_deposit = 0
        cumulative_withdrawn = 0

        traded_value_by_symbol = {}

        while date <= end_date:
            # apply trades from this day
            deposit = 0
            withdrawn = 0

            for trade in [t for t in self.trades.trades if t.date == date]:
                self.applyTrade(trade, current_positions)
                symbol = trade.symbol
                trade_value = trade.quantity * trade.price
                if symbol not in traded_value_by_symbol:
                    traded_value_by_symbol[symbol] = {'bought': 0, 'sold': 0}
                if trade.action == 'Buy':
                    deposit += trade_value
                    traded_value_by_symbol[symbol]['bought'] += trade_value
                elif trade.action == 'Sell' and trade.symbol != 'FB':
                    withdrawn += trade_value
                    traded_value_by_symbol[symbol]['sold'] += trade_value

            cumulative_deposit += deposit
            cumulative_withdrawn += withdrawn

            value = 0
            gain = 0
            non_fb_value = 0
            non_fb_gain = 0
            for position in current_positions.values():
                current_value = self.priceHistory.positionValue(date, position)
                current_gain = current_value - position.costBasis
                value += current_value
                gain += current_gain
                if position.symbol != 'FB':
                    non_fb_value += current_value
                    non_fb_gain += current_gain

            aggregate_perf.append(AggregatePerfRow(
                date,
                value,
                gain,
                non_fb_value,
                non_fb_gain,
                deposit,
                withdrawn,
                non_fb_value - cumulative_deposit + cumulative_withdrawn
            ))
            date += day

        final_positions = []
        for position in current_positions.values():
            symbol = position.symbol
            value = self.priceHistory.positionValue(end_date, position)
            gain = value - position.costBasis
            traded_value = traded_value_by_symbol[symbol] if symbol in traded_value_by_symbol else {'bought': 0, 'sold': 0}
            net_final_value = value + traded_value['sold'] - traded_value['bought']
            net_gain = net_final_value - position.startValue
            if position.startQuantity == 0 and position.quantity == 0 and traded_value['bought'] == 0:
                continue
            final_positions.append(FinalPosition(
                symbol,
                position.startValue,
                position.startQuantity,
                value,
                position.quantity,
                gain,
                traded_value['bought'],
                traded_value['sold'],
                0 if value == 0 else gain / value,
                0 if position.startValue == 0 else net_gain / position.startValue,
            ))
        return (aggregate_perf, final_positions)

if __name__ == "__main__":
    #Portfolio().state()
    Portfolio().timeSeries(datetime.fromisoformat('2021-01-01'), Utils.today())