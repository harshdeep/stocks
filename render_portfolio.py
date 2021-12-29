from datetime import datetime, timedelta
from utils import Utils
from portfolio import Portfolio
from typing import List, Dict
from matplotlib import pyplot as plt
from matplotlib import ticker as tick
import argparse
import numpy as np
from send_email import EmailSender

class RenderPortfolio:
    def __init__(self) -> None:
        self.portfolio = Portfolio()

    def timeseries(self, start_date: datetime, end_date: datetime):
        (aggregate_perf, final_positions) = self.portfolio.timeSeries(start_date, end_date)

        # write local csv files
        date_range_str = Utils.dateRangeStr(start_date, end_date)
        Utils.writeCSV(f'Timeseries {date_range_str}.csv', aggregate_perf)
        Utils.writeCSV(f'Stocks {date_range_str}.csv', final_positions)

        chart_filename = self.renderAggregatePerfChart(aggregate_perf, start_date, end_date)
        summary = self.finalPositionSummary(final_positions)
        summaryMarkdown = self.finalPositionSummaryMarkdown(summary, start_date, end_date)

        EmailSender.sendMarkdown(f'Investment summary {date_range_str}', summaryMarkdown, [chart_filename])

    def lastNDays(self, n:int):
        end_date = Utils.today()
        start_date = end_date - timedelta(days=n)
        self.timeseries(start_date, end_date)

    def lastWeek(self):
        self.lastNDays(7)

    def lastMonth(self):
        self.lastNDays(30)

    def lastQuarter(self):
        self.lastNDays(90)

    def lastYear(self):
        self.lastNDays(365)

    def ytd(self):
        end_date = Utils.today()
        start_date = datetime(year=end_date.year, month=1, day=1)
        self.timeseries(start_date, end_date)

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

    def stockPriceHistoryToPlot(self, symbol: str, start_date: datetime, end_date: datetime, scale_to: float):
        series = self.portfolio.priceHistory.priceHistory(symbol, start_date, end_date)
        # adjust for scale
        i=0
        while np.isnan(series[i]):
            i+=1
        multiplier = scale_to / series[i]
        return [multiplier * v for v in series]

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('period', choices=['week', 'month', 'quarter', 'year', 'ytd', 'test'])
    args = parser.parse_args()
    rp = RenderPortfolio()

    period = args.period
    if period == 'week':
        rp.lastWeek()
    elif period == 'month':
        rp.lastMonth()
    elif period == 'quarter':
        rp.lastQuarter()
    elif period == 'year':
        rp.lastYear()
    elif period == 'ytd':
        rp.ytd()
    elif period == 'test':
        print("Test 123\n")