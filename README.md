# Stocks

After you clone the repository

## Setup
1. Create a ./data folder within this folder
2. Within the data folder, we need two files:
    1. starting_positions.csv represents the positions you hold at the beginning. It has 4 columns
        1. Symbol
        2. Quantity (number of shares)
        3. Cost Basis (total money you spent to buy those shares)
        4. Account (name of the account where you hold these)
    2. trades.csv represents the trades you're going to make now. This has 6 columns
        1. Date
        2. Action (this can be 'Buy', 'Sell', or 'RSU')
        3. Symbol
        4. Quantity (number of shares bought, sold or granted)
        5. Price (per share)
        6. Account (where you made the trade)
3. Now run `python fetch_price_history.py fresh`. This will create a prices.csv file in the /data folder with price history of all stocks that are declared in starting_positions.csv and trades.csv.
4. Create a ./artifacts folder within the main folder
5. Run `python render_portfolio.py ytd` to see your YTD performance. It also accepts "month", "week", and "quarter" as arguments. It will create 3 artifacts in ./artifacts:
    1. A .png with graphs showing day-to-day performance, including comparison with VTI
    2. A Stocks*.csv that shows performance of individual stocks over this time.
    3. A Timeseries*.csv that shows the aggregate day-by-day performance.
6. Create an email_config.py file in this folder and add the following information:
```
email = {
    'from': 'sender_email_address@gmail.com',
    'password': 'password',
    'to': 'receiver_email_address@gmail.com',
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 465,
}
```
7. Now run `python render_portfolio.py ytd --dest email` and it will send you a nicely formatted email.
8. To see which lots are at a loss right now, and can potentially be harvested for taxes: `python lot_analysis.py losses --thresh 0.9` (lists lots that have lost 10% ot more of their value)
9. Utility to list which accounts hold a particular symbol: `python lot_analysis.py accounts --sym AAPL`
10. Set up launchd jobs to automate receiving these emails and to update the price history. Check out the /launchd folder in the code repo for examples.