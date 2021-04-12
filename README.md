# cryptoRealTimePriceAndAlert

Get cryptocurrencies price in real time. Also you can send an email alert if your desired cryptocurrency reach specific price.

## Technologies

**Python 3.8**

#### Required libraries
- numpy
- pandas
- bs4 (BeautifulSoup)
- python-dotenv
- built-in libs:
  - requests
  - datetime
  - logging
  - time
  - sys
  - os
  - re
  - smtplib
  - ssl
  - email

## How to use

- cryptoRealTimeScrape
  * This script works fine without needing any requisite.
- cryptoRealTimePriceAlert
  * One should set the "SENDER_EMAIL" and "SENDER_PASSWORD" to the .env file. (Remember this works only with gmail)
  * Also you need to enable 'Less secure app access' in your google account. (Go to **google** --> **Manage your google account** --> **Security tab (in left)** --> **Turn Less secure app access on**)

## Acknowledgments

* These scripts were built using [WorldCoinIndex](https://www.worldcoinindex.com/) data.
* Thanks to [Mike](https://github.com/mtodisco10) who helped me with this project.