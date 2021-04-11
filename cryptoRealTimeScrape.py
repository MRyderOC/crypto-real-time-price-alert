import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import datetime
import logging


def createLogger(name: str, fmt: str = '[%(name)s](%(asctime)s): %(levelname)s \t %(message)s', 
                dateformat: str = '%b/%d/%y %I:%M:%S %p', path: str = '') -> logging.getLogger:
    '''
    Create a logger for further use
    '''
    # Making log object for further use and .log file
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    SH = logging.StreamHandler() # Making a Stream Handler for shell usage
    SH.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt=fmt, datefmt=dateformat)
    SH.setFormatter(formatter) # Define the output format for Stream Handler
    logger.addHandler(SH)
    if path:
        logging.basicConfig(filename=path, level=logging.INFO,
                    format=fmt, datefmt=dateformat) # Configuration for .log file
    return logger


def now(logger: logging.getLogger = None) -> str:
    '''
    Return the current time as str
    '''
    l = str(datetime.datetime.today()).split() # get the time
    l[1] = l[1].split('.')[0] # reformat the h:m:s.ml to h:m:s
    logger.info(f"Current time is {'T'.join(l)}") if logger else None
    return 'T'.join(l)


def scrapeCrypto(data: pd.DataFrame, logger: logging.getLogger = None) -> pd.DataFrame:
    '''
    Scraping Real-Time crypto prices from worldcoinindex.com
    data -> DataFrame
    '''
    # GET the url and make a BeautifulSoup object
    logger.info('scrapeCrypto(): GET the page for further use.') if logger else None
    url = 'https://www.worldcoinindex.com/'
    source = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}).text
    soup = bs(source, 'lxml')


    table = soup.find('table', id="myTable").tbody # Find the desired table
    tableList = table.find_all('tr') # Scrape the rows of the table

    logger.info('scrapeCrypto(): Scraping begins!!') if logger else None
    # Extracting data from each row in the table
    for row in tableList:
        dic = {}
        try:
            dic['Ticker'] = row.find('td', class_="ticker").h2.text # Find the ticker from row
            price_td = row.find('td', class_="number pricekoers lastprice") # Find the price tag
            dic['Price'] = price_td.find('span', class_='span').text # Find the price from the tag
        except:
            continue # This exception is because of sume redundant rows that do not have ticker and price
        pd.set_option("display.max_columns", None) # Stop pandas to truncate the view
        data = data.append(pd.Series(dic), ignore_index=True) # Append crypto ticker to DataFrame
    logger.info('scrapeCrypto(): End of scraping. Returning the result.') if logger else None
    return data


def dataCleaning(data: pd.DataFrame, logger: logging.getLogger = None) -> pd.DataFrame:
    '''
    Since the price column of data is not float and it contains extra letter ","
        we need to clean the data for further usage.
    data -> DataFrame
    '''
    logger.info('dataCleaning(): Function starts!!') if logger else None
    def priceCalc(row):
        '''
        Change string price to float
        '''
        s = str(row['Price']).strip()
        return float(''.join(s.split(',')))
    data['Price'] = data.apply(priceCalc, axis='columns') # Apply priceCalc() to whole DataFrame
    logger.info('dataCleaning(): End of function and return the results!') if logger else None
    return data


if __name__ == '__main__':
    logger = createLogger('Crypte Real-Time Scrape')
    logger.info('Prgram Starts!')
    
    # Defining DataFrame
    df = pd.DataFrame(columns=['Ticker', 'Price'])
    # Scraping data
    df = dataCleaning(scrapeCrypto(df, logger), logger)
    
    now(logger)
    print(df)
    
    logger.info('End of program.\n{}'.format('-'*40))
