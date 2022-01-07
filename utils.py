import csv
from datetime import datetime
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

    def today() -> datetime:
        today = datetime.today()
        return datetime(year=today.year, month=today.month, day=today.day)

    def dateToStr(date: datetime) -> str:
        return date.date().isoformat()
    
    def dateRangeStr(start_date: datetime, end_date: datetime) -> str:
        return f'{Utils.dateToStr(start_date)} to {Utils.dateToStr(end_date)}'