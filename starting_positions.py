import csv
from dataclasses import dataclass
import typing

@dataclass
class Position:
    symbol: str
    quantity: float = 0
    costBasis: float = 0
    startValue: float = 0
    startQuantity: float = 0

    def resetStartValue(self):
        self.startValue = self.costBasis
        self.startQuantity = self.quantity

    def costBasisPerShare(self) -> float:
        if self.quantity == 0:
            return 0.0
        return self.costBasis / self.quantity

class StartingPositions:
    FILE_NAME = 'starting_positions.csv'

    def __init__(self) -> None:
        self.positions: typing.Dict[str, Position] = {}

    def load(self):
        if self.positions:
            print("Starting position data has already been loaded")
            return

        with open(self.FILE_NAME) as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row['Symbol']
                quantity = float(row['Quantity'])
                cost_basis = float(row['Cost Basis'])
                # ignoring account for now
                if symbol not in self.positions:
                    self.positions[symbol] = Position(symbol)
                self.positions[symbol].quantity += quantity
                self.positions[symbol].costBasis += cost_basis
                self.positions[symbol].resetStartValue()

if __name__ == "__main__":
    sp = StartingPositions()
    sp.load()
    print(sp.positions['VTI'])