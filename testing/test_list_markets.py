import poloniex
from pprint import pprint
import sys
import time

polo = poloniex.Poloniex()

ticker = polo.returnTicker()

markets_btc = []
markets_eth = []
markets_xmr = []
markets_usdt = []
for product in ticker:
    pair = key.split('_')
    #print(pair)
    if pair[0] == 'BTC':
        markets_btc.append(pair)
        reply_message = 'BTC Markets:\n'
    elif pair[0] == 'ETH':
        markets_eth.append(pair)
        reply_message = 'ETH Markets:\n'
    elif pair[0] == 'XMR':
        markets_xmr.append(pair)
        reply_message = 'XMR Markets:\n'
    elif pair[0] == 'USDT':
        markets_usdt.append(pair)
        reply_message = 'USDT Markets:\n'

markets = []
for currency in markets_btc:
    markets.append(currency[1])
print(markets)

time.sleep(5)

markets.sort()
print(markets)

time.sleep(5)

loop_count = 0
for currency in markets_btc:
    loop_count += 1
    reply_message = reply_message + currency[1] + '\n'
print(reply_message)
