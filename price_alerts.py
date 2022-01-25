import argparse
from datetime import timedelta
from typing import List, MutableSet
from portfolio import FinalPosition, Portfolio
from price_history import PriceHistory
from utils import Utils
from send_email import EmailSender
import numpy as np

class PriceAlerts:
    priceHistory: PriceHistory
    activePositions: MutableSet[str]
    alerts: List[str]

    def __init__(self) -> None:
        portfolio = Portfolio()
        self.priceHistory = portfolio.priceHistory
        self.positions = portfolio.activePositions()
        self.alerts = []
        
    def gen(self):
        today = Utils.today()
        yesterday = today - timedelta(days=1)
        for symbol in self.priceHistory.prices:
            if symbol not in self.positions:
                continue
            today_price = self.priceHistory.price(today, symbol)
            yesterday_price = self.priceHistory.price(yesterday, symbol)
            mean_50 = self.priceHistory.movingAverage(symbol, 50)
            mean_200 = self.priceHistory.movingAverage(symbol, 200)

            if yesterday_price >= mean_50 and mean_50 >= today_price:
                self.alerts.append(f'{symbol} dipped under 50da {Utils.currency(mean_50)}')
            if yesterday_price <= mean_50 and mean_50 <= today_price:
                self.alerts.append(f'{symbol} went above 50da {Utils.currency(mean_50)}')

            if yesterday_price >= mean_200 and mean_200 >= today_price:
                self.alerts.append(f'{symbol} dipped under 200da {Utils.currency(mean_200)}')
            if yesterday_price <= mean_200 and mean_200 <= today_price:
                self.alerts.append(f'{symbol} went above 200da {Utils.currency(mean_200)}')

            diff = (today_price - yesterday_price) / yesterday_price
            if abs(diff) > 0.05:
                self.alerts.append(f'{symbol} moved by {Utils.percent(diff)}')

            if today_price >= self.priceHistory.max(symbol, 50):
                self.alerts.append(f'{symbol} at 50 day high {Utils.currency(today_price)}')

            if today_price <= self.priceHistory.min(symbol, 50):
                self.alerts.append(f'{symbol} at 50 day low {Utils.currency(today_price)}')

    def render(self) -> str:
        self.gen()
        alerts_str = '\n'.join([f'* {alert}' for alert in self.alerts])
        return f'''
# Stock alerts
{alerts_str}
            '''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dest', choices=['console', 'email'], default='console')
    args = parser.parse_args()
    dest = args.dest

    alerts = PriceAlerts()
    alerts_markdown = alerts.render()

    if dest == 'console':
        print(alerts_markdown)
    else:
        EmailSender.sendMarkdown('Stock alerts', alerts_markdown, [])

if __name__ == "__main__":
    main()