import cryptoRealTimeScrape as RealTimeCrypto
import pandas as pd
import logging
import datetime; import time
import sys
import os
import re
import smtplib; import ssl
from email.mime.text import MIMEText as MT; from email.mime.multipart import MIMEMultipart as MM
from dotenv import load_dotenv


class Alert:
    '''
    This class acts as alert manager.
    It stores ticker name with the desired range.
    Also it has a flag variable which prevent us to send an alert twice.
    '''
    _ticker: str # Name of ticker
    _low: float # Low boundary of the desired range
    _high: float # High boundary of the desired range
    _visited: bool # Specify if we already sent an alert or not

    def __init__(self, ticker, low, high):
        self._ticker = ticker.upper()
        self._low = low
        self._high = high
        self._visited = False
    
    def getInfo(self):
        '''Returns all information about current alert.'''
        return self._ticker, self._low, self._high, self._visited
    
    def visit(self):
        '''Make this alert visited. (Alert sent!!)'''
        self._visited = True
    
    def getTicker(self):
        '''Returns ticker name.'''
        return self._ticker


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


def get_prices_realtime(logger: logging.getLogger = None) -> pd.DataFrame:
    '''
    Get the real-time prices using cryptoRealTimeScrape module
    '''
    logger.info('get_prices_realtime(): GET the prices real-time!') if logger else None
    return RealTimeCrypto.dataCleaning(RealTimeCrypto.scrapeCrypto(pd.DataFrame({'Ticker': [], 'Price':[]})))


def get_email(logger: logging.getLogger = None) -> str:
    '''
    Get client's email.
    '''
    logger.info("get_email(): Get client's email.") if logger else None
    def checkMail(email: str, logger: logging.getLogger = None) -> bool:
        '''
        Check if email is valid email or not. Return True if it's valid else False.
        '''
        logger.info("checkMail(): Check for valid email.") if logger else None
        # Split the string to domain and prefix
        try:
            prefix, domain = email.split('@')
        except:
            return False
        
        # Check length constrains and creating re.match()
        if len(prefix) > 64:
            return False
        else:
            # Match prefix using re
            prefixMatch = re.match(r'^[a-zA-Z0-9_.+-]+', prefix)
        if len(domain) > 253:
            return False
        else:
            # Match domain using re
            domainMatch = re.match(r'[a-zA-Z0-9-]+[.][a-zA-Z0-9-.]+', domain)
        
        return True if (domainMatch and prefixMatch) else False

    s = input('Please enter your email address: ')
    return s if checkMail(s, logger) else print('Please enter a VALID email.')


def get_info_priceAlert(logger: logging.getLogger = None) -> list:
    '''
    Get desired cryptos list along with low and high prices
    '''
    logger.info("get_info_priceAlert(): Get desired crypto list along with the range.") if logger else None
    l = [] # To store the whole data
    print('For exit enter -1')
    while True:
        ticker = input('Please enter the crypto ticker: ')
        # Check for exit condition
        if ticker == '-1':
            break
        high = float(input('Please enter the high boundary: '))
        low = float(input('Please enter the low boundary: '))
        # Check if entry data is valid
        if high < 0 or low < 0:
            print('Please enter VALID data')
            continue
        l.append(Alert(ticker, low, high)) # Store the data
    logger.info("get_info_priceAlert(): Return the desired cryptos as a list.") if logger else None
    return l


def sendMail(ticker: str, price: int, email: str, high_low: bool, logger: logging.getLogger = None):
    '''
    high_low -> bool: True if price is higher than expected else False
    '''
    logger.info("sendMail(): Sending mail to {} using SMTP for {}.".format(email, ticker)) if logger else None
    
    load_dotenv()
    senderEmail = os.getenv('SENDER_EMAIL')
    senderPass = os.getenv('SENDER_PASSWORD')

    logger.info("sendMail(): Creating message!") if logger else None
    msg = MM() # Create MIMEMultipart object
    msg['To'] = email # Add sender email
    msg['From'] = senderEmail # Add reciever email
    msg['Subject'] = 'Price Alert' # Add Subject
    # Create email content as HTML
    if high_low:
        caption = '{} reached your HIGH price and current price is: {}'.format(ticker, price)
    else:
        caption = '{} reached your LOW price and current price is: {}'.format(ticker, price)
    HTML = '''
    <html>
        <body>
            <h1>Crypto Price Alert!!</h1>
            <h2>'''+ caption +''' </h2>
        </body>
    </html>
    '''
    MTObj = MT(HTML, 'html') # Create a html MIMEText object
    msg.attach(MTObj) # Attach the MTObj into message container

    logger.info("sendMail(): Creating connection and login process.") if logger else None
    SSLcontext = ssl.create_default_context() # Create a secure socket layer (SSL) context object 
    server = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465, context=SSLcontext) # Create a Simple Mail Transfer Protocol (SMTP) connection
    server.login(senderEmail, senderPass) # Login to email account
    server.sendmail(senderEmail, email, msg.as_string()) # Send the mail
    logger.info("sendMail(): Email sent!!!") if logger else None


def checkPrice(data: pd.DataFrame, alerts: list, email: str, logger: logging.getLogger = None):
    '''
    Check if the current price is above or below alert price.
        If it is, send an email to client email address.
    '''
    logger.info("checkPrice(): Compare the current price with client's desired prices") if logger else None
    # Change the data which is DataFrame to dict() for easier comparison
    d = {}
    tickers = data['Ticker'].to_dict()
    prices = data['Price'].to_dict()
    for item in tickers:
        d[tickers[item]] = prices[item]
    del tickers, prices

    # Check every ticker in client desired tickers
    for item in alerts:
        ticker, low, high, visited = item.getInfo()
        if not visited: # If alert haven't sent yet
            price = d[ticker]
            if price <= low:
                sendMail(ticker, price, email, False, logger) # If price is below the range, send a False flag
                item.visit()
            elif price >= high:
                sendMail(ticker, price, email, True, logger) # If price is above the range, send a True flag
                item.visit()
            else:
                continue # If price is in the range, do nothing


def realtimePriceAlert(alerts: list, email: str, timer: int = 30, logger: logging.getLogger = None):
    '''
    Set a timer for constantly checking the price and send an alert if needed
    '''
    logger.info("realtimePriceAlert(): Send an alert with timer set to {} seconds.".format(timer)) if logger else None
    tickers = [item.getTicker() for item in alerts] # Store all desired tickers by their name
    visited = [alert[3] for alert in [item.getInfo() for item in alerts]] # Store all desired tickers visited attribute
    while sum(visited) != len(tickers):
        df = get_prices_realtime(logger) # GET real time prices and store them in df
        logger.info(f'realtimePriceAlert(): Prices:\n {df.loc[df.Ticker.isin(tickers)]}')
        checkPrice(df.loc[df.Ticker.isin(tickers)], alerts, email, logger) # Extract desired tickers from df and pass it to checkPrice
        visited = [alert[3] for alert in [item.getInfo() for item in alerts]] # Update visited
        time.sleep(timer)


if __name__ == '__main__':
    logger = createLogger('Crypto Price Alert')
    clientEmail = get_email(logger)

    clientData = get_info_priceAlert(logger)
    if clientEmail:
        realtimePriceAlert(clientData, clientEmail, logger=logger)
    else:
        sys.exit('Invalid email. Try Again!!!')