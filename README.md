import numpy
import talib

close = numpy.random.random(10)
output = talib.EMA(close, timeperiod=5)
