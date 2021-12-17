import csv

class StartingPositions:
    FILE_NAME = 'starting_positions.csv'

    def __init__(self) -> None:
        self.positions = {}

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
                    self.positions[symbol] = {'quantity': 0, 'cost_basis': 0}
                self.positions[symbol]['quantity'] += quantity
                self.positions[symbol]['cost_basis'] += cost_basis

if __name__ == "__main__":
    sp = StartingPositions()
    sp.load()
    print(sp.positions['VTI'])