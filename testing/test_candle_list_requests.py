import json
import numpy as np
import poloniex
from pprint import pprint
import requests
from talib.abstract import *
import time

api_url = 'https://poloniex.com/'
api_command = 'public?command=returnChartData'
api_pair = '&currencyPair=BTC_STR'
api_start = '&start=1517689800'
api_end = '&end=9999999999'
api_period = '&period=1800'

#https://poloniex.com/public?command=returnChartData&currencyPair=BTC_STR&start=1517689800&end=9999999999&period=1800

api_request = api_url + api_command + api_pair + api_start + api_end + api_period
r = requests.get(api_request)
data = r.json()
print(data)

time.sleep(5)

candles = np.array(data)
print(candles)

output = SMA(candles, timeperiod=25, price='close')
print(output)

#macd, signal, histogram = MACD(np_close, fastperiod=12, slowperiod=26, signalperiod=9)
