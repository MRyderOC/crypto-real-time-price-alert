# crypto-real-time-price-alert

Get cryptocurrencies prices in real time.

Send an email alert if your desired cryptocurrency passes a specific price.

## Technologies

**Python 3.8**
#### You can find required libraries in requirements.txt.

## How to use

## How to use
1. Clone the repo: ``` git clone "https://github.com/MRyderOC/crypto-real-time-price-alert.git" ```.
2. Create a virtual environment: ```python3 -m venv myenv```.
3. Activate the virtual environment: ```source myenv/bin/activate```
4. Install dependencies: ```pip3 install -r requirements.txt```.
5. Store the "SENDER_EMAIL" and "SENDER_PASSWORD" to the .env file.
   > ***Remember this works only with gmail.***
   > 
   > Also you need to enable 'Less secure app access' in your google account. (Go to **google** --> **Manage your google account** --> **Click on Security tab on left sidebar** --> **Turn Less secure app access ON.**)
6. Run the script: ```python3 PriceAlert.py```.
7. Enter the receiver email.
8. Enter desired tickers and boundary prices.
9. Sit back and Relax!
10. See the price alert email in your inbox!

## Acknowledgments

* These scripts were built using [WorldCoinIndex](https://www.worldcoinindex.com/) data.
* Thanks to [Mike](https://github.com/mtodisco10) who helped me with this project.
