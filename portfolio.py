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
    totalCostBasis: float
    totalValue: float
    totalGain: float
    nonFBCostBasis: float
    nonFBValue: float
    nonFBGain: float
    deposits: float
    withdrawals: float
    netNonFBValue: float
    dayNonFBGain: float

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
    currentPrice: float
    mean50Day: float
    mean200Day: float
    gainOnStartValue: float
    gainOnMean50Day: float
    gainOnMean200Day: float

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

    def timeSeries(self, start_date, end_date) -> Tuple[List[AggregatePerfRow], List[FinalPosition]]:
        current_positions = self.startingPositions.positions.copy()
        date = self.trades.trades[0].date
        assert(date <= start_date)
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

        aggregate_perf: List[AggregatePerfRow] = []
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

            cost_basis = 0
            value = 0
            gain = 0
            non_fb_value = 0
            non_fb_gain = 0
            non_fb_cost_basis = 0
            for position in current_positions.values():
                current_value = self.priceHistory.positionValue(date, position)
                current_gain = current_value - position.costBasis
                value += current_value
                gain += current_gain
                cost_basis += position.costBasis
                if position.symbol != 'FB':
                    non_fb_value += current_value
                    non_fb_gain += current_gain
                    non_fb_cost_basis += position.costBasis

            day_non_fb_gain = 0
            if len(aggregate_perf) > 0:
                day_non_fb_gain = (non_fb_value - aggregate_perf[-1].nonFBValue)/aggregate_perf[-1].nonFBValue

            aggregate_perf.append(AggregatePerfRow(
                date,
                cost_basis,
                value,
                gain,
                non_fb_cost_basis,
                non_fb_value,
                non_fb_gain,
                deposit,
                withdrawn,
                non_fb_value - cumulative_deposit + cumulative_withdrawn,
                day_non_fb_gain
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
            current_price = self.priceHistory.price(end_date, symbol)
            mean_50d = self.priceHistory.movingAverage(symbol, 50)
            mean_200d = self.priceHistory.movingAverage(symbol, 200)
            final_positions.append(FinalPosition(
                symbol,
                position.startValue,
                position.startQuantity,
                value,
                position.quantity,
                gain,
                traded_value['bought'],
                traded_value['sold'],
                current_price,
                mean_50d,
                mean_200d,
                0 if position.startValue == 0 else net_gain / position.startValue * 100,
                (current_price - mean_50d) / mean_50d * 100,
                (current_price - mean_200d) / mean_200d * 100,
            ))
        return (aggregate_perf, final_positions)

if __name__ == "__main__":
    Portfolio().timeSeries(datetime.fromisoformat('2021-01-01'), Utils.today())