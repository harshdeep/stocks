from datetime import datetime, timedelta
from price_history import PriceHistory
from send_email import EmailSender
from starting_positions import Position, StartingPositions
from trades import Trade, Trades
from utils import Utils
from typing import List, Dict
from matplotlib import pyplot as plt
from matplotlib import ticker as tick
import numpy as np

class CurrentState:
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

    def computeOverall(self):
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

        Utils.writeCSV(f'State {Utils.dateToStr(today)}.csv', result)
        Utils.print_currency('Overall gain', total_gain)
        Utils.print_currency('Non-FB gain', total_non_fb_gain)

    def stockPriceHistoryToPlot(self, symbol: str, start_date: datetime, end_date: datetime, scale_to: float):
        series = self.priceHistory.priceHistory(symbol, start_date, end_date)
        i=0
        while np.isnan(series[i]):
            i+=1
        multiplier = scale_to / series[i]
        return [multiplier * v for v in series]

    def computeTimeSeries(self, start_date, end_date):
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

            aggregate_perf.append({
                'date': date,
                'total_value': value,
                'total_gain': gain,
                'non_fb_value': non_fb_value,
                'non_fb_gain': non_fb_gain,
                'deposit': deposit,
                'withdrawn': withdrawn,
                'net_non_fb_value': non_fb_value - cumulative_deposit + cumulative_withdrawn
            })
            date += day

        date_range_str = Utils.dateRangeStr(start_date, end_date)
        Utils.writeCSV(f'Timeseries {date_range_str}.csv', aggregate_perf)

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
            final_positions.append({
                'symbol': symbol,
                'start_value': position.startValue,
                'start_quantity': position.startQuantity,
                'value': value,
                'quantity': position.quantity,
                'gain': gain,
                'gain_on_current_value': 0 if value == 0 else gain / value,
                'bought': traded_value['bought'],
                'sold': traded_value['sold'],
                'gain_on_start_value': 0 if position.startValue == 0 else net_gain / position.startValue,
            })
        
        Utils.writeCSV(f'Stocks {date_range_str}.csv', final_positions)
        return(aggregate_perf, final_positions)

    def finalPositionSummary(self, final_positions):
        summary = {}
        sorted_by_gain = sorted(final_positions, key=lambda x: x['gain'])
        summary['absolute_gain'] = {
            'losers': sorted_by_gain[:5],
            'winners': list(reversed(sorted_by_gain[-5:])),
        }

        sorted_by_percent_gain = sorted(final_positions, key=lambda x: x['gain_on_start_value'])
        summary['percent_gain'] = {
            'losers': sorted_by_percent_gain[:5],
            'winners': list(reversed(sorted_by_percent_gain[-5:])),
        }

        summary['bought'] = sorted(list(filter(lambda x: x['bought'] != 0, final_positions)), key=lambda x: x['bought'], reverse=True)
        summary['sold'] = sorted(list(filter(lambda x: x['sold'] != 0, final_positions)), key=lambda x: x['sold'], reverse=True)
        return summary

    def finalPositionSummaryMarkdown(self, summary, start_date, end_date):
        absolute_gain_strings = {}
        for key, positions in summary['absolute_gain'].items():
            absolute_gain_strings[key] = ''
            for position in positions:
                absolute_gain_strings[key] += f"| {position['symbol']} | {Utils.currency(position['gain'])} | \n"

        percent_gain_strings = {}
        for key, positions in summary['percent_gain'].items():
            percent_gain_strings[key] = ''
            for position in positions:
                percent_gain_strings[key] += f"| {position['symbol']} | {position['gain_on_start_value'] * 100:.0f}% | \n"

        transaction_strings = {}
        for transaction in ['bought', 'sold']:
            transaction_strings[transaction] = ''
            for position in summary[transaction]:
                transaction_strings[transaction] += f"| {position['symbol']} | {Utils.currency(position[transaction])} | \n"
        
        text = f"""
## Summary from {Utils.dateRangeStr(start_date, end_date)}

### Biggest winners
| Symbol | Delta |
| ---    | ---  |
{absolute_gain_strings['winners']}

### Biggest losers
| Symbol | Delta |
| ---    | ---  |
{absolute_gain_strings['losers']}

### Biggest winners by percent
| Symbol | Delta |
| ---    | ---  |
{percent_gain_strings['winners']}

### Biggest losers by percent
| Symbol | Delta |
| ---    | ---  |
{percent_gain_strings['losers']}

### Bought
| Symbol | Amount |
| ---    | ---  |
{transaction_strings['bought']}

### Sold
| Symbol | Amount |
| ---    | ---  |
{transaction_strings['sold']}
        """
        return text

    def renderAggregatePerfChart(self, aggregate_perf: List[Dict], start_date: datetime, end_date: datetime) -> str:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

        fig.set_size_inches(20, 15)
        fig.set_dpi(100)

        ax1.set_xlabel('Date')
        ax1.set_ylabel('Value')
        ax1.grid()

        ax1.get_yaxis().set_major_formatter(tick.FuncFormatter(lambda x, _: Utils.currency(x)))
        
        dates = [r['date'] for r in aggregate_perf]

        non_fb_value = [r['non_fb_value'] for r in aggregate_perf]
        net_non_fb_value = [r['net_non_fb_value'] for r in aggregate_perf]

        ax1.plot(dates, non_fb_value, label='Value')
        ax1.plot(dates, net_non_fb_value, label='Net value')
        ax1.plot(dates, self.stockPriceHistoryToPlot('VTI', start_date, end_date, non_fb_value[0]), label = 'VTI')

        min_index = np.argmin(non_fb_value)
        ax1.annotate(
            Utils.currency(non_fb_value[min_index]),
            (dates[min_index], non_fb_value[min_index]),
            color='red'
        )

        max_index = np.argmax(non_fb_value)
        ax1.annotate(
            Utils.currency(non_fb_value[max_index]),
            (dates[max_index], non_fb_value[max_index]),
            color='green'
        )

        ax1.annotate(
            Utils.currency(non_fb_value[-1]),
            (dates[-1], non_fb_value[-1]),
            color='black'
        )

        ax2.set_ylabel('Gain')
        ax2.get_yaxis().set_major_formatter(tick.FuncFormatter(lambda x, _: Utils.currency(x)))
        ax2.grid()
        non_fb_gain = [r['non_fb_gain'] for r in aggregate_perf]
        ax2.plot(dates, non_fb_gain, label='Gain')
        min_index = np.argmin(non_fb_gain)
        ax2.annotate(
            Utils.currency(non_fb_gain[min_index]),
            (dates[min_index], non_fb_gain[min_index]),
            color='red'
        )

        max_index = np.argmax(non_fb_gain)
        ax2.annotate(
            Utils.currency(non_fb_gain[max_index]),
            (dates[max_index], non_fb_gain[max_index]),
            color='green'
        )

        ax2.annotate(
            Utils.currency(non_fb_gain[-1]),
            (dates[-1], non_fb_gain[-1]),
            color='black'
        )

        ax3.bar(dates, [r['deposit'] for r in aggregate_perf], color='blue')
        ax3.bar(dates, [-1*r['withdrawn'] for r in aggregate_perf], color='red')
        ax3.set_ylabel('Transactions')
        ax3.grid()

        ax1.legend()
        filename = f'Plot {Utils.dateRangeStr(start_date, end_date)}.png'
        plt.savefig(filename)
        print(f'\nWrote {filename}')
        return filename

    def monthlySummary(self):
        end_date = Utils.today()
        start_date = end_date - timedelta(days=30)
        return self.summary(start_date, end_date)

    def ytdSummary(self):
        end_date = Utils.today()
        start_date = datetime(year = end_date.year, month = 1, day = 1)
        return self.summary(start_date, end_date)

    def summary(self, start_date, end_date):
        (aggregate_perf, final_positions) = self.computeTimeSeries(start_date, end_date)
        filename = self.renderAggregatePerfChart(aggregate_perf, start_date, end_date)
        summary = self.finalPositionSummary(final_positions)
        markdownStr = self.finalPositionSummaryMarkdown(summary, start_date, end_date)
        return (markdownStr, filename)

if __name__ == "__main__":
    #CurrentState().computeOverall()

    print("Monthly Summary")
    text, img_filename = CurrentState().monthlySummary()
    EmailSender.sendMarkdown("Monthly investment summary", text, [img_filename])

    #print("YTD summary")
    #CurrentState().ytdSummary()