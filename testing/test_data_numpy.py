from decimal import *
import json
import numpy as np
import poloniex
from pprint import pprint
import time

polo = poloniex.Poloniex()

data = polo.returnChartData('BTC_STR', period=1800)

#pprint(data)
#print()
#pprint(data[0])
#pprint(data[10])
#pprint(data[20])
#print()

candle_array = []
key_array = []
for x in range(0, len(data)):
    candle = data[x]
    
    candle_list = []
    key_list = []
    for k, v in candle.items():
        candle_list.append(v)
        key_list.append(k)
    
    #candle_array[x] = candle_list
    candle_array.append(candle_list)
    #key_array[x] = key_list
    key_array.append(key_list)

"""
pprint(candle_array)
print()
print(len(candle_array))
print()
pprint(candle_array[0])
print()
pprint(candle_array[10])
print()
pprint(candle_array[20])
print()

time.sleep(1)
"""

print(key_array[0])
print(key_array[10])
print(key_array[20])

time.sleep(3)

data_array = np.stack(np.array(candle_array, dtype=float), axis=-1)
print(data_array)
print(data_array[0])
print(data_array[1])
print(data_array[2])
print(data_array[3])
print(data_array[4])
print(data_array[5])
print(data_array[6])
print(data_array[7])
print(type(data_array[7]))
