import poloniex
from pprint import pprint
import time

polo = poloniex.Poloniex()
ticker = polo.returnTicker()

markets_btc = []
markets_eth = []
markets_xmr = []
markets_usdt = []

for key in ticker:
    pair = key.split('_')
    if pair[0] == 'BTC':
        markets_btc.append(key)
    elif pair[0] == 'ETH':
        markets_eth.append(key)
    elif pair[0] == 'XMR':
        markets_xmr.append(key)
    elif pair[0] == 'USDT':
        markets_usdt.append(key)

print('BTC MARKETS')
pprint(markets_btc)
#time.sleep(3)
#print('ETH MARKETS')
#pprint(markets_eth)
#time.sleep(3)
#print('XMR MARKETS')
#pprint(markets_xmr)
#time.sleep(3)
#print('USDT MARKETS')
#pprint(markets_usdt)
#time.sleep(3)

print()
print('Done!')
