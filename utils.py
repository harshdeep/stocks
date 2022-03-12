import csv
from datetime import datetime, date
from dataclasses import asdict

class Utils:
    def currency(value):
        return f'${value:,.0f}'.replace('$-', '-$')

    def percent(value):
        return f'{value * 100:.2f}%'

    def print_currency(context, value):
        print(f'{context}: {Utils.currency(value)}')

    def writeCSV(filename, rows):
        with open(filename, 'w') as f:
            writer = csv.DictWriter(f, fieldnames = rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    def writeCSVObjects(filename, rows):
        Utils.writeCSV(filename, [asdict(r) for r in rows])

    def today() -> date:
        return datetime.today().date()

    def dateToStr(date: date) -> str:
        return date.isoformat()
    
    def dateRangeStr(start_date: date, end_date: date) -> str:
        return f'{Utils.dateToStr(start_date)} to {Utils.dateToStr(end_date)}'

    def log(s: str) -> None:
        print(f'{datetime.now().strftime("%m/%d, %H:%M:%S")}: {s}')