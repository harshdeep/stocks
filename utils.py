import csv
from datetime import datetime

class Utils:
    def print_currency(context, value):
        print(f'{context}: ${value:,.0f}'.replace('$-', '-$'))

    def writeCSV(filename, rows):
        with open(filename, 'w') as f:
            writer = csv.DictWriter(f, fieldnames = rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    def today() -> datetime:
        today = datetime.today()
        return datetime(year=today.year, month=today.month, day=today.day)