from datetime import datetime, timedelta
from os import pathsep
from trades import Trades, Trade
from typing import Dict, List, Set
from price_history import PriceHistory
from utils import Utils
import argparse

class Lot:
    trade: Trade
    remainingQuantity: float
    initialValue: float
    currentValue: float

    def __init__(self, trade: Trade) -> None:
        self.trade = trade
        self.remainingQuantity = self.trade.quantity

    def computeValue(self, price_history: PriceHistory) -> None:
        self.initialValue = self.remainingQuantity * self.trade.price
        self.currentValue = self.remainingQuantity * price_history.price(Utils.today(), self.trade.symbol)

    def toDict(self) -> Dict:
        return {
            'Account': self.trade.account,
            'Symbol': self.trade.symbol,
            'Date': Utils.dateToStr(self.trade.date),
            'Initial Value': self.initialValue,
            'Current Value': self.currentValue,
            'Loss': self.currentValue - self.initialValue,
            'Percent Loss': (self.currentValue - self.initialValue)/self.initialValue,
            'Remaining Quantity': self.remainingQuantity,
            'Initial Quantity': self.trade.quantity,
            'Long term': self.trade.date < datetime.today() - timedelta(days=365)
        }

class LotAnalysis:
    FILE_NAME = 'artifacts/loss_lots.csv'

    potentialLots: List[Lot]

    def __init__(self) -> None:
        self.trades = Trades()
        self.trades.load()
        self.priceHistory = PriceHistory()
        self.boughtLots = self.lotsFromTrades('Buy')
        self.soldLots = self.lotsFromTrades('Sell')
        self.balanceLots()

    def lotsFromTrades(self, action: str) -> Dict[str, Dict[str, List[Lot]]]:
        lots = {}
        for trade in filter(lambda t: t.action == action, self.trades.trades):
            if trade.account not in lots:
                lots[trade.account] = {}
            if trade.symbol not in lots[trade.account]:
                lots[trade.account][trade.symbol] = []
            lots[trade.account][trade.symbol].append(Lot(trade))
        return lots


    def balanceLots(self) -> None:
        # Fuzzy matching of lots. Assumes first bought first sold
        for account in self.boughtLots:
            if account not in self.soldLots:
                continue
            for symbol in self.boughtLots[account]:
                if symbol not in self.soldLots[account]:
                    continue
                for bought_lot in self.boughtLots[account][symbol]:
                    for sold_lot in self.soldLots[account][symbol]:
                        if bought_lot.remainingQuantity > sold_lot.remainingQuantity:
                            bought_lot.remainingQuantity -= sold_lot.remainingQuantity
                            sold_lot.remainingQuantity = 0
                        else:
                            sold_lot.remainingQuantity -= bought_lot.remainingQuantity
                            bought_lot.remainingQuantity = 0

    def lotsAtLoss(self, threshold: float) -> List[Lot]:
        potentialLots = []
        for account in self.boughtLots:
            for symbol in self.boughtLots[account]:
                for lot in self.boughtLots[account][symbol]:
                    if lot.remainingQuantity == 0:
                        continue
                    lot.computeValue(self.priceHistory)
                    if lot.currentValue < threshold * lot.initialValue:
                        potentialLots.append(lot)
        return potentialLots

    def lossByAccount(self, potentialLots: List[Lot]) -> Dict[str, float]:
        lossByAccount = {}
        for lot in potentialLots:
            if lot.trade.account not in lossByAccount:
                lossByAccount[lot.trade.account] = 0
            lossByAccount[lot.trade.account] += (lot.currentValue - lot.initialValue)
        return lossByAccount

    def accountsHoldingSymbol(self, symbol: str) -> Set[str]:
        accounts = set()
        for account in self.boughtLots:
            if symbol in self.boughtLots[account]:
                for lot in self.boughtLots[account][symbol]:
                    if lot.remainingQuantity > 0:
                        accounts.add(account)
                        continue
        return accounts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('func', choices=['losses', 'accounts'])
    parser.add_argument('-t', '--thresh', type=float, default=0.8)

    parser.add_argument('-s', '--sym', default='VTI')
    args = parser.parse_args()

    la = LotAnalysis()

    if args.func == 'losses':
        lots = la.lotsAtLoss(args.thresh)
        Utils.writeCSV(la.FILE_NAME, [lot.toDict() for lot in lots])
        print(f'Wrote {la.FILE_NAME}')
        for account, loss in la.lossByAccount(lots).items():
            print(f'{account}\t{Utils.currency(loss)}')
    elif args.func == 'accounts':
        accounts = la.accountsHoldingSymbol(args.sym)
        if len(accounts) == 0:
            print(f'No accounts hold {args.sym}')
        else:
            account_list = ', '.join(accounts)
            print(f'Following accounts hold {args.sym}: {account_list}')
        
if __name__ == "__main__":
    main()