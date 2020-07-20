import numpy
import talib

close = numpy.random.random(10)
output = talib.EMA(close, timeperiod=5)


close = numpy.delete(close, 0)
close = numpy.append(close, 2.5)