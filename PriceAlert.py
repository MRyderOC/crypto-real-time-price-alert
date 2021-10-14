from datetime import datetime
import time
import threading
import logging
import os
import re
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
from dotenv import load_dotenv

from RealTimeScrape import scrape_crypto


class Alert:
    """
    This class acts as alert manager.
    It stores ticker name with the desired range.
    Also it has a flag variable which prevent us to send an alert twice.
    """
    _ticker: str
    _low: float
    _high: float
    _visited: bool

    def __init__(self, ticker, low, high):
        self._ticker = ticker.upper()
        self._low = low
        self._high = high
        self._visited = False

    def get_info(self):
        """Returns all information about current alert."""
        return self._ticker, self._low, self._high, self._visited

    def visit(self):
        """Make this alert visited. (Alert sent!!)."""
        self._visited = True

    def get_ticker(self):
        """Returns ticker name."""
        return self._ticker


def create_logger(name: str, path: str = '') -> logging.getLogger:
    """
    Pass a name and get a logger.

    Parameters
    ----------
    name: str

    path: str
        Default: ''
        Path of where the logs will be store.
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


def now() -> str:
    return datetime.today().strftime("%Y-%m-%d %H:%M:%S")


def is_valid_mail(email: str) -> bool:
    # Split the string to domain and prefix
    try:
        prefix, domain = email.split('@')
    except ValueError:
        return False

    # Check length constrains and creating re.match()
    if len(prefix) > 64:
        return False
    else:
        # Match prefix using re
        prefix_match = re.match(r'^[a-zA-Z0-9_.+-]+', prefix)
    if len(domain) > 253:
        return False
    else:
        # Match domain using re
        domain_match = re.match(r'[a-zA-Z0-9-]+[.][a-zA-Z0-9-.]+', domain)

    return True if (domain_match and prefix_match) else False


def get_email() -> str:
    """Get client's email."""
    s = input('Please enter your email address: ')
    return s if is_valid_mail(s) else print('Please enter a VALID email.')


def get_info_price_alert() -> list:
    """Get desired cryptos list along with low and high prices."""
    data = []
    print('For exit enter -1.')
    while True:
        ticker = input('Please enter the crypto ticker: ')
        # Check for exit condition
        if ticker == '-1':
            break
        high = float(input('Please enter the high boundary: '))
        low = float(input('Please enter the low boundary: '))
        # Check if entry data is valid
        if high < 0 or low < 0:
            print('Please enter VALID data.')
            continue
        data.append(Alert(ticker, low, high))
    return data


def send_mail(
    ticker: str,
    price: int,
    receiver_email: str,
    high_low: bool,
    logger: logging.getLogger = None
):
    """
    Send an email for receiver_email with the context of the ticker
    and its price and specialized variable high_low.

    ticker: str
        Name of the ticker that should send the alert for.

    price: int
        Current price of ticker.

    receiver_email: str
        An email which alerts will be sent to.

    high_low: bool
        Pass True if price is higher than expected else False.

    logger: logging.getLogger
        Default: None
    """
    if logger:
        logger.info(
            f"send_mail(): Sending mail to {receiver_email} using SMTP for {ticker}."
        )

    # Load environment variables
    load_dotenv()
    sender_email = os.getenv('SENDER_EMAIL')
    sender_pass = os.getenv('SENDER_PASSWORD')

    # Creating the message
    msg = MIMEMultipart()
    msg['to'], msg['from'] = receiver_email, sender_email
    msg['subject'] = 'Price Alert'
    html = (
        '<html><body>'
        '<h1>Crypto Price Alert!!</h1><h2>'
        f'{ticker} reached your'
        f' {"HIGH" if high_low else "LOW"}'
        f' price and current price is: {price}'
        '</h2></body></html>'
    )
    msg.attach(MIMEText(html, 'html'))

    if logger:
        logger.info("send_mail(): Creating connection and login process.")

    # Create SMTP session for sending the mail
    with SMTP("smtp.gmail.com", 587) as smtp_session:
        smtp_session.starttls()
        smtp_session.login(sender_email, sender_pass)
        smtp_session.sendmail(sender_email, receiver_email, msg.as_string())
    if logger:
        logger.info("send_mail(): Email sent!")


def check_price(
    data: pd.DataFrame,
    alerts: list,
    receiver_email: str,
    logger: logging.getLogger = None
):
    """
    Send an email to the client email address if the current price is above or below alert price.

    data: pd.DataFrame
        A DataFrame contains Tickers along their Price and Percentage.

    alerts: list
        A list of Alert objects.

    receiver_email: str
        An email which alerts will be sent to.

    logger: logging.getLogger
        Default: None
    """
    if logger:
        logger.info("check_price(): Compare the current price with client's desired prices")

    # Limit our DataFrame to the tickers that we're looking for
    df = data[
        data['Ticker'].isin([alert.get_ticker() for alert in alerts])
    ].set_index("Ticker")

    for alert in alerts:
        ticker, low, high, visited = alert.get_info()
        if not visited:
            price = df.at[ticker, "Price"]
            if price <= low:
                # If price is below the range, send a False flag
                send_mail(ticker, price, receiver_email, False, logger)
                alert.visit()
            elif price >= high:
                # If price is above the range, send a True flag
                send_mail(ticker, price, receiver_email, True, logger)
                alert.visit()
            else:
                continue  # If price is in the range, do nothing


def real_time_price_alert(
    alerts: list,
    receiver_email: str,
    timer: int = 10,
    logger: logging.getLogger = None
):
    """
    Set a timer for constantly checking the price and send an alert if needed.

    Parameteres
    -----------
    alerts: list
        A list of Alert objects.

    receiver_email: str
        An email which alerts will be sent to.

    timer: int
        Default: 10
        Time between each two consecutive calls.

    logger: logging.getLogger
        Default: None
    """
    if logger:
        logger.info(
            f"real_time_price_alert(): Send an alert with timer set to {timer} seconds."
        )
    tickers = [alert.get_ticker() for alert in alerts]
    while not all([item.get_info()[3] for item in alerts]):
        df = scrape_crypto(logger)
        logger.info(
            f"real_time_price_alert(): Prices:\n {df.loc[df['Ticker'].isin(tickers)]}"
        )
        check_price(df.loc[df['Ticker'].isin(tickers)], alerts, receiver_email, logger)
        tickers = [
            alert.get_ticker()
            for alert in alerts
            if not alert.get_info()[3]
        ]
        time.sleep(timer)


def crypto_price_alert(
    alerts: list,
    receiver_email: str,
    timer: int = 10,
    logger: logging.getLogger = None
):
    alert_thread = threading.Thread(
        target=real_time_price_alert,
        args=(
            alerts,
            receiver_email,
            timer,
            logger
        )
    )
    alert_thread.start()


if __name__ == '__main__':
    logger = create_logger('Crypto Price Alert')

    client_email = get_email()
    while not client_email:
        print('Invalid email. Try Again!!!\nTo exit press Ctrl+C.')
        client_email = get_email()

    client_data = get_info_price_alert()
    crypto_price_alert(client_data, client_email, logger=logger)

