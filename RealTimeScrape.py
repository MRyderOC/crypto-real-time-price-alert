import logging

import pandas as pd
import requests
from bs4 import BeautifulSoup as bs


def create_logger(
    name: str,
    path: str = ''
) -> logging.getLogger:
    """
    Pass a name and get a logger.

    Parameters
    ----------
    name: str

    path: str
        Default: ''
        path the logs will be store.
    """
    # Making log object for further use and .log file
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # Making a Stream Handler for shell usage
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    # Define the output format for Stream Handler
    sh.setFormatter(logging.Formatter(
        fmt='[%(asctime)s  %(name)s] %(levelname)s: %(message)s',
    ))
    logger.addHandler(sh)
    # Configuration for .log file
    if path:
        logging.basicConfig(
            filename=path,
            level=logging.INFO,
            format='[%(asctime)s  %(name)s]: %(levelname)s \t %(message)s',
        )
    return logger


def scrape_crypto(logger: logging.getLogger = None) -> pd.DataFrame:
    """Scraping Real-Time crypto prices from worldcoinindex.com."""

    if logger:
        logger.info('scrape_crypto(): Start scraping.')

    # Get the source page
    url = 'https://www.worldcoinindex.com/'
    response = requests.get(
        url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    if not response.ok:
        raise Exception("Didn't get 200 response. Try again.")
    soup = bs(response.text, 'lxml')

    # Store the data in a DataFrame
    data = pd.DataFrame(columns=['Ticker', 'Price'])
    table_list = soup.find('table', id="myTable").tbody.find_all('tr')  # Find the desired table
    for row in table_list:
        dic = {}
        try:
            dic['Ticker'] = row.find('td', class_="ticker").h2.text  # Find the ticker
            price_td = row.find('td', class_="number pricekoers lastprice")  # Find the price tag
            dic['Price'] = price_td.find('span', class_='span').text  # Find the price from tag
            dic['Percentage'] = row.find('td', class_="percentage").span.text  # Find the percentage
        except Exception:
            # Skip some redundant rows that do not have ticker and price
            continue
        data = data.append(pd.Series(dic), ignore_index=True)

    # Clean the data
    data['Price'] = data.apply(
        lambda row: float(''.join(str(row['Price']).strip().split(','))),
        axis='columns'
    )
    data['Percentage'] = data.apply(
        lambda row: float(str(row['Percentage']).strip()[:-1]),
        axis='columns'
    )

    return data


if __name__ == '__main__':
    logger = create_logger('RealTimeScrape.py')
    logger.info('Program Starts!')

    pd.set_option("display.max_columns", None)
    df = scrape_crypto(logger)

    print(df)

    logger.info('End of program.\n{}'.format('-'*40))
