from trades import Trades
from starting_positions import StartingPositions

class Watchlist:
    def load():
        watchlist = set()
        
        [watchlist.add(symbol) for symbol in StartingPositions().load()]
        [watchlist.add(t.symbol) for t in Trades().load()]

        # for comparison graphs
        watchlist.add('VTI')

        return watchlist

if __name__ == "__main__":
    print(Watchlist.load())