import numpy
import talib
from talib import MA_Type

close = numpy.random.random(100)
#output = talib.SMA(close)
#print(output)

upper, middle, lower = talib.BBANDS(close, matype=MA_Type.T3)
print(upper)
print(middle)
print(lower)

output = talib.MOM(close, timeperiod=5)
print(output)
