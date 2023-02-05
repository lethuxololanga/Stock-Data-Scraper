import requests
from bs4 import BeautifulSoup
import csv

my_stocks = ['HNST', 'KODK', 'NOK', 'SFIX', 'GPRO', 'SPCE', 'FTCH', 'TME', 'BCS', 'HOOD', 'SNAP', 'NIO', 'LCID', 'DB', 'F', 'CVNA', 'WBD', 'COUR', 'CPNG', 'ASAN', 'SSL', 'AFRM', 'T', 'RIVN', 'MANU', 'TRIP', 'DBX', 'SQSP', 'HMC', 'PARA', 'BMBL', 'PINS', 'INTC', 'DOCN', 'UBER', 'BOX', 'GSK', 'BP', 'U', 'CMCSA', 'GM', 'VZ', 'DELL', 'FVRR', 'PFE', 'Z', 'WFC', 'CSCO', 'EBAY', 'C', 'SHOP', 'JD', 'SHEL', 'DASH', 'NET', 'KO', 'NDAQ', 'LOGI', 'TWLO', 'K', 'STX', 'COIN',
             'SSTK', 'DDOG', 'ZM', 'SQ', 'PYPL', 'ORCL', 'WWE', 'WIX', 'SONY', 'MS', 'GRMN', 'AMZN', 'SBUX', 'GOOGL', 'GOOG', 'BABA', 'DIS', 'EA', 'EXPE', 'ABNB', 'SPOT', 'COF', 'VMW', 'CROX', 'NKE', 'IBM', 'JPM', 'WMT', 'BIDU', 'TM', 'TMUS', 'ETSY', 'AAPL', 'JNJ', 'PEP', 'CVX', 'CRM', 'TGT', 'AXP', 'WDAY', 'META', 'TSLA', 'UPS', 'NVDA', 'FDX', 'V', 'CAT', 'MSFT', 'RACE', 'MCD', 'EL', 'LULU', 'MCO', 'ZBRA', 'HD', 'HUBS', 'NFLX', 'MA', 'ADBE', 'COST', 'BLK', 'BKNG']


def getData(symbol):

    """
    Retrieve stock information for the given stock symbol from Yahoo Finance.

    Arguments:
        symbol (str): The stock symbol to retrieve information for.

    Returns:
        stock (dict): A dictionary containing the stock symbol, price, and price change.
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    url = f'https://finance.yahoo.com/quote/{symbol}'
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    stock = {
        'symbol': symbol,
        'price': soup.find('div', {'class': 'D(ib) Mend(20px)'}).find_all('span')[0].text,
        'change': soup.find('div', {'class': 'D(ib) Mend(20px)'}).find_all('span')[1].text,
    }

    return stock


fieldnames = ['symbol', 'price', 'change']

with open('stockdata.csv', 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for item in my_stocks:
        stock = getData(item)
        print('Getting data for:', item)
        writer.writerow(stock)
