#
  # Stock Data Scraper

This program is a simple web scraper that retrieves the current stock price and change of a given list of stocks. The stock data is then saved to a CSV file.

#
  # Requirements


'Python 3.x'
'requests'
'BeautifulSoup4'
'csv'

#
  # Usage


1. Clone the repository to your local machine.

    $ git clone https://github.com/<username>/stock-data-scraper.git

2. Install the required packages using pip.

    $ pip install -r requirements.txt

3. Open the script in a text editor and modify the my_stocks list to include the stock symbols you want to retrieve data for.

4. Run the script.

    $ python stock-data-scraper.py

5. The stock data will be saved to a CSV file named stockdata.csv. The file will be created in the same directory as the script.

#
  # Customization


You can add additional fields to the stock dictionary to include additional data such as the stock's name, market, etc. Just make sure to add the corresponding field name to the fieldnames list and add the appropriate code to the getData function.
You can also change the name of the CSV file by modifying the with open statement at the bottom of the script.
#
