import csv
from dataclasses import dataclass
from typing import Dict

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
    FILE_NAME = 'data/starting_positions.csv'

    def __init__(self) -> None:
        self.positions: Dict[str, Position] = {}

    def load(self) -> Dict[str, Position]:
        if self.positions:
            print("Starting position data has already been loaded")
            return self.positions

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
        return self.positions

if __name__ == "__main__":
    sp = StartingPositions()
    sp.load()
    print(sp.positions['VTI'])