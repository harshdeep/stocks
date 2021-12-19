
class Utils:
    def print_currency(context, value):
        print(f'{context}: ${value:,.0f}'.replace('$-', '-$'))