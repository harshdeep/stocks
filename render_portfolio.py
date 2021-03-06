from datetime import datetime, timedelta, date
from posixpath import join
from utils import Utils
from portfolio import AggregatePerfRow, FinalPosition, Portfolio
from typing import Final, List, Dict
from matplotlib import pyplot as plt
from matplotlib import ticker as tick
import argparse
import numpy as np
from send_email import EmailSender
from dataclasses import asdict

class FinalSummary:
    absoluteWinners: List[FinalPosition]
    absoluteLosers: List[FinalPosition]
    percentWinners: List[FinalPosition]
    percentLosers: List[FinalPosition]
    bought: List[FinalPosition]
    sold: List[FinalPosition]
    startDate: date
    endDate: date
    finalPerf: AggregatePerfRow

    def __init__(self, final_positions: List[FinalPosition], aggregate_perf: List[AggregatePerfRow], start_date: date, end_date: date) -> None:
        self.finalPerf = aggregate_perf[-1]
        sorted_by_gain = sorted(final_positions, key=lambda x: x.gain)
        self.absoluteWinners = list(reversed(sorted_by_gain[-5:]))
        self.absoluteLosers = sorted_by_gain[:5]

        sorted_by_percent_gain = sorted(final_positions, key=lambda x: x.gainOnStartValue)
        self.percentWinners = list(reversed(sorted_by_percent_gain[-5:]))
        self.percentLosers = sorted_by_percent_gain[:5]

        self.bought = sorted(list(filter(lambda x: x.bought != 0, final_positions)), key=lambda x: x.bought, reverse=True)
        self.sold = sorted(list(filter(lambda x: x.sold != 0, final_positions)), key=lambda x: x.sold, reverse=True)

        self.startDate = start_date
        self.endDate = end_date

    def rows(self, positions: List[FinalPosition], renderFunc) -> str:
        return '\n'.join([f'| {p.symbol} | {renderFunc(p)} |' for p in positions])

    def markdown(self) -> str:
        text = f"""
## Summary from {Utils.dateRangeStr(self.startDate, self.endDate)}
### Overall: {Utils.currency(self.finalPerf.totalGain)}, {Utils.percent(self.finalPerf.totalGain / self.finalPerf.totalCostBasis)}
### Non FB: {Utils.currency(self.finalPerf.nonFBGain)}, {Utils.percent(self.finalPerf.nonFBGain / self.finalPerf.nonFBCostBasis)}

### Biggest winners
| Symbol | Delta |
| ---    | ---  |
{self.rows(self.absoluteWinners, lambda p: Utils.currency(p.gain))}

### Biggest losers
| Symbol | Delta |
| ---    | ---  |
{self.rows(self.absoluteLosers, lambda p: Utils.currency(p.gain))}

### Biggest winners by percent
| Symbol | Delta |
| ---    | ---  |
{self.rows(self.percentWinners, lambda p: Utils.percent(p.gainOnStartValue/100.0))}

### Biggest losers by percent
| Symbol | Delta |
| ---    | ---  |
{self.rows(self.percentLosers, lambda p: Utils.percent(p.gainOnStartValue/100.0))}

### Bought
| Symbol | Amount |
| ---    | ---  |
{self.rows(self.bought, lambda p: Utils.currency(p.bought))}

### Sold
| Symbol | Amount |
| ---    | ---  |
{self.rows(self.sold, lambda p: Utils.currency(p.sold))}
        """
        return text

class RenderPortfolio:
    def __init__(self, dest: str) -> None:
        self.portfolio = Portfolio()
        self.dest = dest

    def timeseries(self, start_date: date, end_date: date):
        date_range_str = Utils.dateRangeStr(start_date, end_date)

        Utils.log(f'Computing timeseries {date_range_str}')
        (aggregate_perf, final_positions) = self.portfolio.timeSeries(start_date, end_date)

        # write local csv files
        Utils.log('Writing CSVs')
        Utils.writeCSVObjects(f'artifacts/Timeseries {date_range_str}.csv', aggregate_perf)
        Utils.writeCSVObjects(f'artifacts/Stocks {date_range_str}.csv', final_positions)

        Utils.log('Rendering Chart')
        chart_filename = self.renderAggregatePerfChart(aggregate_perf, start_date, end_date)

        Utils.log('Generating markdown')
        summaryMarkdown = FinalSummary(final_positions, aggregate_perf, start_date, end_date).markdown()

        if self.dest == "console":
            print(summaryMarkdown)
        elif self.dest == "email":
            Utils.log('Sending email')
            EmailSender.sendMarkdown(f'Investment summary {date_range_str}', summaryMarkdown, [chart_filename])
            Utils.log('Sent email')
        else:
            raise Exception(f'Unknown dest {self.dest}')

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
        start_date = datetime(year=end_date.year, month=1, day=1).date()
        self.timeseries(start_date, end_date)

    def renderAggregatePerfChart(self, aggregate_perf: List[AggregatePerfRow], start_date: date, end_date: date) -> str:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1)

        fig.set_size_inches(20, 15)
        fig.set_dpi(100)

        ax1.set_xlabel('Date')
        ax1.set_ylabel('Value')
        ax1.grid()

        ax1.get_yaxis().set_major_formatter(tick.FuncFormatter(lambda x, _: Utils.currency(x)))
        
        dates = [r.date for r in aggregate_perf]

        non_fb_value = [r.nonFBValue for r in aggregate_perf]
        net_non_fb_value = [r.netNonFBValue for r in aggregate_perf]

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
        non_fb_gain = [r.nonFBGain for r in aggregate_perf]
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

        ax3.bar(dates, [r.deposits for r in aggregate_perf], color='blue')
        ax3.bar(dates, [-1*r.withdrawals for r in aggregate_perf], color='red')
        ax3.set_ylabel('Transactions')
        ax3.grid()

        ax1.legend()
        filename = f'artifacts/Plot {Utils.dateRangeStr(start_date, end_date)}.png'
        plt.savefig(filename)
        Utils.log(f'\nWrote {filename}')
        return filename

    def stockPriceHistoryToPlot(self, symbol: str, start_date: date, end_date: date, scale_to: float):
        series = self.portfolio.priceHistory.priceHistory(symbol, start_date, end_date)
        # adjust for scale
        i=0
        while np.isnan(series[i]):
            i+=1
        multiplier = scale_to / series[i]
        return [multiplier * v for v in series]

def main():
    Utils.log("Start render_portfolio")
    parser = argparse.ArgumentParser()
    parser.add_argument('period', choices=['week', 'month', 'quarter', 'year', 'ytd', 'test'])
    parser.add_argument('-d', '--dest', choices=['console', 'email'], default='console')
    args = parser.parse_args()
    rp = RenderPortfolio(args.dest)

    Utils.log(args)

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

def test():
    rp = RenderPortfolio('console')
    rp.ytd()

if __name__ == "__main__":
    main()
    #test()