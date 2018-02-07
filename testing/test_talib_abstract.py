import numpy as np
from talib.abstract import *

inputs = {
    'open': np.random.random(100),
    'high': np.random.random(100),
    'low': np.random.random(100),
    'close': np.random.random(100),
    'volume': np.random.random(100)
}

upper, middle, lower = BBANDS(inputs, 20, 2, 2)
print(upper)
print(middle)
print(lower)

output = SMA(inputs, timeperiod=25)
print(output)
