# Returns the middle indices of a range. 
# The middle one if the range is even, the middle two if the range is odd numbered
from pprint import pprint
import numpy

# first return value: middle indices
# second return value: number of indices right or left of middle

def determineMiddleRight(startIndex, endIndex):
    
    if (startIndex > endIndex):
        endIndex, startIndex = startIndex, endIndex
        
    indexRange = range(startIndex, endIndex + 1)
    numRange = len(indexRange)
    middleright = startIndex + (numRange // 2)
    return middleright, numRange

def determineMiddleIndices(startIndex, endIndex):
    
    middleright, numRange = determineMiddleRight(startIndex, endIndex)
  #  numberSideIndices = endIndex - middleright
    if (numRange % 2 == 0) :
         #even number of middle LEDs -> take the middle two to show the correct tuning
        return [(middleright - 1),  (middleright)]#, numberSideIndices
    else : 
        #odd number of middle LEDs -> take the single middle to show the correct tuning
        return [middleright] #, numberSideIndices
       
# determine the number of Indices starting from one side, including the middle one       
def determineNumberSideIndices(startIndex, endIndex):
    middleright, numRange = determineMiddleRight(startIndex, endIndex)
    return endIndex - middleright + 1 
    
# range for the LEDs to display. LEDs between start and endIndex are used
# minValue and maxValue give the range of the numbers assigned to the LEDs 
# between min and maxIndex -> e.g. tuner: -.5 .. +.5 
class rangeDict(object):
    
    def __init__(self, startIndex, endIndex, minValue, maxValue):
        
        switch = False
        
        if endIndex < startIndex :
            #raise ValueError('endIndex must be higher than startIndex')
            switch = True

        self.startIndex = startIndex
        self.endIndex = endIndex
        self.minValue = minValue
        self.maxValue = maxValue
        
         
        
        if not switch:
            self.indexRange = range(startIndex, endIndex + 1)
        else :
            self.indexRange = range(endIndex, startIndex + 1)
        

        self.numRange = len(self.indexRange)
        step = (float(self.maxValue - self.minValue)) / float(self.numRange)
       
        print "minvalue: {}".format(self.minValue)
        print "maxvalue: {}".format(self.maxValue)
        print "step: {}".format(step)
        print "numRange: {}".format(self.numRange)
        self.valueRanges = numpy.arange(minValue, maxValue, step)
        self.valueDict = dict()
        
        lower = 0
        # fill dictionary
        if not switch: 
            lower = self.minValue
        else:
            lower = self.maxValue
        
        for i, indexRangePosition in zip(range(self.numRange), self.indexRange) :
            
            if not switch:
                upper = lower + step
            else :
                upper = lower - step
                
            self.valueDict[indexRangePosition] = [lower, upper]
            lower = upper
            print i
            print self.valueDict[indexRangePosition]
            
    def getRangeIndex(self, floatVal, reversed=False):
            if (floatVal < self.minValue) or (floatVal > self.maxValue):
                raise ValueError("Value out of bounds")
            
            if reversed :
                for index, valueRange in self.valueDict.items():
                    if valueRange[0] > floatVal > valueRange[1] : return index
            else :
                for index, valueRange in self.valueDict.items():
                    if valueRange[0] < floatVal < valueRange[1] : return index
            return 0 

#second return value determines if value is out of bounds
class linearInterpolation(object):
    
    def __init__(self, minX, maxX, minY, maxY):
       
        if (minX > maxX):
            raise ValueError("minX must be smaller than maxX")
        
            
        self.minX = minX
        self.maxX = maxX
            
        self.minY = minY
        self.maxY = maxY
        
        self.deltaX = maxX - minX
        self.deltaY = maxY - minY
    
    def interpolate(self, xVal):
        
        if(xVal < self.minX) : 
            return self.minY, True
        
        elif(xVal > self.maxX) :
            return self.maxY, True
        
        else :
            return self.minY + (xVal - self.minX) * (self.deltaY / self.deltaX), False
        
# interpolate between two parallel line functions in the form y = a*x + b
# b is the value to be interpolated. Values range between ymin and ymax, 
# so values greater ymax will equal to ymax and smaller values than ymin to ymin 
class yaxb(object):
    
    def __init__(self, minX, midX, maxX, minY, maxY, n):
        if( not(minX < midX < maxX)): 
            raise ValueError("minX must be smaller than midX must be smaller than maxX")
        
        self.minX = float(minX)
        self.midX = float(midX)
        self.maxX = float(maxX)
        self.minY = float(minY)
        self.maxY = float(maxY)
        self.n = float(n)
        
        self.deltaX = midX - minX
        self.a = (self.maxY - self.minY) / (self.maxX - self.midX)
        
    def interpolate(self, xVal, index):
        
        b = self.maxY - self.a * (self.maxX - (float(index) / self.n) * self.deltaX)
     #   print("i = {0}".format(index))
     #   print("b = {0}".format(b))
     
        
        yVal = self.a * xVal + b
    #    print("xVal = {0}, yVal = {1}".format(xVal, yVal))
        
        
        if(yVal > self.maxY):
            return self.maxY
        
        elif(yVal < self.minY):
            return self.minY
        
        else :
            return yVal

# one field to interpolate all values for the side indices
class yaxbField(object):
    def __init__(self, minX, midX, maxX, minY, maxY, numberOfIndices):
        if( not(minX < midX < maxX)): 
            raise ValueError("minX must be smaller than midX must be smaller than maxX")
        self.minX = float(minX)
        self.midX = float(midX)
        self.maxX = float(maxX)
        self.minY = float(minY)
        self.maxY = float(maxY)
        self.nOfIndices = numberOfIndices
        
        self.yaxbObj = yaxb(self.minX, self.midX, self.maxX, self.minY, self.maxY, self.nOfIndices)
                            
        
    def interpolate(self, xVal):
        
        values = []
        for i in range(self.nOfIndices):
            values.append(self.yaxbObj.interpolate(xVal, i))
        
        return values
            
        
                
#rd = rangeDict(10, 33, -0.5, 0.5)
#pprint(rd.valueDict)

# linterPol = linearInterpolation(0,1, 6000, 5000)
# print(linterPol.interpolate(0.13183))
# print(linterPol.interpolate(-1))
# print(linterPol.interpolate(5))

# ya = yaxb(100,5000,10000, 40, 300, 7)
# 
# for i in range(7) :
#     print("i = {0}, interpol = {1}".format(i, ya.interpolate(7000, i)))
