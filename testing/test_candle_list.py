import json
import numpy as np
import poloniex
from pprint import pprint
import requests
from talib.abstract import *
import time

polo = poloniex.Poloniex()
data = polo.returnChartData('BTC_STR', period=1800)

candles = np.array(data)
output = SMA(candles, timeperiod=25, price='close')
pprint(output)

#macd, signal, histogram = MACD(np_close, fastperiod=12, slowperiod=26, signalperiod=9)
