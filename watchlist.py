from trades import Trades
from starting_positions import StartingPositions

class Watchlist:
    def load():
        watchlist = set()
        
        starting_positions = StartingPositions()
        starting_positions.load()
        for symbol in starting_positions.positions.keys():
            watchlist.add(symbol)

        trades = Trades()
        trades.load()
        for trade in trades.trades:
            watchlist.add(trade['symbol'])

        return watchlist

if __name__ == "__main__":
    print(Watchlist.load())