from lpd8806.LPD8806 import *
from time import sleep
from pdlmUtils import *
from pprint import pprint
from collections import deque
from pdlmUtils import *
from pdlmSettings import pdlmSettings
from pdlmEnums import TimeSignatures
from itertools import cycle
COLOROFF = ColorHSV(0,0,1)

########################################################################
#################fields for chasing light animations ###################
########################################################################

# "abstract" super Class for  
class ledDict(object):
    def __init__(self, ledsAndGaps):
        
        self.arrayLength = sum(ledsAndGaps)
        self.ledIndexList = list()
        self.colorDeque = deque(list(), self.arrayLength) 
    #    self.numLEDs = numLEDs
        
    
    def shiftUp(self, color):
        self.colorDeque.appendleft(color)
    
    def shiftDown(self, color):
        self.colorDeque.append(color)
        
    
    def printColors(self):
        
        for color in self.colorDeque:
            print("indices: {0} - Color(H:{1}, S:{2}, V:{3})"
                  .format(color, 
                          color.H, 
                          color.S,
                          color.V))
            
    def printColorPairs(self):
        for i in range(len(self.ledIndexList)):
            print("LED indices: {0}, Color(H:{1}, S:{2}, V:{3})".format(
                            self.ledIndexList[i],
                            self.colorDeque[i].H,
                            self.colorDeque[i].S,
                            self.colorDeque[i].V))

    def getLowerBoundColor(self):
        
        return self.colorDeque[0]       
    
   


# ledsAndGaps should be a sequence of integers in the following order:
# gaplength, fieldlength, gaplength, fieldlength. If you don't want
# delay between fields, simply put a 0 or just sum the fields together  
class linear(ledDict): 
    def __init__(self, ledsAndGaps, reversed = False):
        ledDict.__init__(self, ledsAndGaps)
      
       

        ledIndex = 0
        for i in range(len(ledsAndGaps)):
            
            # we have a value for colors here
            if i % 2 == 0:
                
               
                
                #append colors
                self.colorDeque.extend([COLOROFF for j in range(ledsAndGaps[i])])
                
                #append led indices
                self.ledIndexList.extend(([ledIndex + k]) for k in range(ledsAndGaps[i]))
                
                #update ledIndex                
                ledIndex = ledIndex + ledsAndGaps[i]
                
               
                
            # we have encountered a gap
            else :
                
                 #append colors
                self.colorDeque.extend([COLOROFF for j in range(ledsAndGaps[i])])
#                pprint("colorDeque {}".format(self.colorDeque))
                
                #append None for led indices
                self.ledIndexList.extend(None for k in range(ledsAndGaps[i]))
       #         pprint("ledIndexList {}".format(self.ledIndexList))
                
   #             print("new LED index: {0}".format(ledIndex))
        if reversed :
            self.ledIndexList = self.ledIndexList[::-1]
            self.colorDeque.reverse()
            
        self.printColorPairs()
    def isGap(self, index):
       return self.ledIndexList[index] == None


# used for animations, which start in the middle of all LEDs
# ledsAndGaps should be a sequence of integers in the following order:
# gaplength, fieldlength, gaplength, fieldlength. If you don't want
# delay between fields, simply put a 0 or just sum the fields together  
# only works for symmetrical orders
class middleAltogether(ledDict):
    def __init__(self, ledsAndGaps, startingFromMiddle=True):
        ledDict.__init__(self, ledsAndGaps)
        #put it in a linear list first, to be able to determine, if a certain index is a gap or not
        lgaps = linear(ledsAndGaps, False)
        
        self.numLEDs = sum(x for x in ledsAndGaps[0::2]) # lst[start:stop:step] <- starting with the element 1 with a step size of 2 gives all even numbers
        
    #    print("numLEDs: {}".format(self.numLEDs))
        
        totalNumber = sum(x for x in ledsAndGaps)
       
        #determine middle indices
        # the middleIndices here are the middleIndices of the total number, including gaps 
        numberSideIndices = determineNumberSideIndices(0, len(lgaps.colorDeque) - 1)
        middleIndices = determineMiddleIndices(0, self.numLEDs - 1)
        
     #   print("middleIndices: {0} , numberSideIndices: {1}".format(middleIndices, numberSideIndices))
        
        iterator = range(0)
        # iterator is reversed if the sequence should start from the middle
        if startingFromMiddle : 
            iterator = reversed(range(numberSideIndices))  
            rightIndex = middleIndices[0] if len(middleIndices) == 1 else middleIndices[1]
            leftIndex = middleIndices[0]
        else :
            iterator = range(numberSideIndices)
            rightIndex = self.numLEDs - 1
            leftIndex = 0
            
        # virtualIndex is the number of steps on one side, including the gaps
        # it is used to check, if an index is a gap or not
        for virtualIndex in iterator : #reversed(range(numberSideIndices)):
            
            
            #fill the lists from bottom up
            if lgaps.isGap(virtualIndex):
                self.colorDeque.append(COLOROFF)
   #             pprint("colorDeque {}".format(self.colorDeque))
                
                #append None for LED indices
                self.ledIndexList.append(None)
 #               pprint("ledIndexList {}".format(self.ledIndexList))
            else :
                
               
                self.colorDeque.append(COLOROFF)
                #append LED indices for both sides
                self.ledIndexList.append(list([leftIndex, rightIndex]))
  #              pprint("ledIndexList {}".format(self.ledIndexList))
                
                if startingFromMiddle :
                    rightIndex += 1
                    leftIndex -= 1
                else :
                    rightIndex -= 1
                    leftIndex += 1
                    
                
            
        
        
# used for animations, which are equally displayed in each field
# ledsAndGaps: only fields with their lengths, no gaps
# todo: assign different color ranges to each field (boy, this would look awesome
# or all the same
# 
class middleFields(ledDict):
    def __init__(self, ledsAndGaps, inout = True):
        ledDict.__init__(self, ledsAndGaps)
        
        ledIndex = 0
        
        # the maximum length of the lists is half of the maximum field length
        maxlength = determineNumberSideIndices(0, max(ledsAndGaps))
        
        # initialize the colorDeque with COLOROFF for the maximum Number of indices in a field
        self.colorDeque = deque(list(), maxlength) 
        self.colorDeque.extend([COLOROFF for j in range(maxlength)])
        self.ledIndexList = list([None]) * maxlength
        
        # iterate over fields
        for i in range(len(ledsAndGaps))[0::2]:
            
 #           print("i = {0}, len(ledsAndGaps) = {1}".format(i, len(ledsAndGaps)))
            startindex = ledIndex
            endindex = ledIndex + ledsAndGaps[i] - 1
 #           print("startindex: {}".format(startindex))
 #           print("endindex: {}".format(endindex))
            middleIndices = determineMiddleIndices(startindex, endindex)
            numberOfSideIndices = determineNumberSideIndices(startindex, endindex)
            
  #          print("numberOfSideIndices : {}".format(numberOfSideIndices) )
  #          print("middleIndices : {}".format(middleIndices[0], middleIndices[1]) )
             
            if self.ledIndexList[0] == None :
                self.ledIndexList[0] = list()
            self.ledIndexList[0].extend(middleIndices)
            print (self.ledIndexList[0])
            
            
            # iterate over indices in a field
            for j in range(1, numberOfSideIndices) :
#                print("range(1, numberOfSideIndices) {}".format(range(1, numberOfSideIndices)))
                if self.ledIndexList[j] == None :
                    self.ledIndexList[j] = list()
                leftIndex = middleIndices[0] - j
                rightIndex =  (middleIndices[1] if len(middleIndices) > 1 else leftIndex) + j
                self.ledIndexList[j].extend([leftIndex, rightIndex])
                
                
                print (self.ledIndexList[j])
                
            ledIndex = ledIndex + ledsAndGaps[i]
            
            # reverse the deque if direction is out -> in
        if not inout :
            self.colorDeque.reverse()

#same as middleFields, but the colors move from one side to the other         
class leftRightFields(ledDict):
    def __init__(self, ledsAndGaps, leftToRight = True):
        ledDict.__init__(self, ledsAndGaps)
        
        ledIndex = 0
        
        # the maximum length of the lists is half of the maximum field length
        maxlength = max(ledsAndGaps)
        
        # initialize the colorDeque with COLOROFF for the maximum Number of indices in a field
        self.colorDeque = deque(list(), maxlength) 
        self.colorDeque.extend([COLOROFF for j in range(maxlength)])
        self.ledIndexList = list([None]) * maxlength
        
        # iterate over fields
        for i in range(len(ledsAndGaps[::2])):
            startindex = ledIndex
            endindex = ledIndex + ledsAndGaps[i*2] - 1
                
            # iterate over indices in a field
            for j in range(0, ledsAndGaps[i*2]) :
                if self.ledIndexList[j] == None :
                    self.ledIndexList[j] = list()
                ind = ledIndex + j
                self.ledIndexList[j].extend([ind])
                
                
            ledIndex = ledIndex + ledsAndGaps[i*2]
            
            # reverse the deque if direction is out -> in
     #   print (leftToRight)
        if not leftToRight :
            self.ledIndexList = self.ledIndexList[::-1]
        #    print("drin")
        
        pprint(self.colorDeque)
        pprint(self.ledIndexList)

                

# colorfields should be a list(list(color)), the inner list being two colors
# to interpolate between two colors from min index to max index,
# or one color if you only want to have one color in the field
class colorFieldsMiddle(object):
    def __init__(self, pdlmsettings):
                 #fields, fieldColors, inout = True):
        #colorFields.__init__(self, pdlmsettings.fields)
        self.fields = pdlmsettings.fields
        self.fieldColors = pdlmsettings.fieldColors
        self.outin = pdlmsettings.orderFieldLEDsOutIn
        self.allFieldsAllColors = list()
        self.initiateColorHues()

     
     
     #set the static hue values for each fields LED indices
    def initiateColorHues(self) :    
         
         
         for fieldIndex in range(len(self.fields)) :

             field = self.fields[fieldIndex]
             fieldColor = self.fieldColors[fieldIndex]
       
             
             middleIndices = determineMiddleIndices(field[0], field[-1])
             numberOfSideIndices = determineNumberSideIndices(field[0], field[-1])
             
             fieldLEDIndexList = list()
             fieldColorDeque = deque(list(), numberOfSideIndices)
             
             #map the range from one color to another across the field
             if len(fieldColor) > 1 : 
                 # interpolation Mapping for the two color's hue values
                 colorMapping = linearInterpolation(middleIndices[-1], middleIndices[-1] + numberOfSideIndices,
                                                    fieldColor[0].H, fieldColor[1].H)
                 
                 saturationMapping = linearInterpolation(middleIndices[-1], middleIndices[-1] + numberOfSideIndices,
                                                    fieldColor[0].S, fieldColor[1].S)
                 valueMapping = linearInterpolation(middleIndices[-1], middleIndices[-1] + numberOfSideIndices,
                                                    fieldColor[0].V, fieldColor[1].V)
                 
             
             #iterate over the side indices in a field to map colors hues to pairs of two indices
                 for i in range(numberOfSideIndices) :
                     print("i: {}".format(i))
                     if i == 0 :
                         fieldLEDIndexList.append(middleIndices)
                         #fieldColorDeque.append(fieldColor[0])
                     else : 
                         fieldLEDIndexList.append([middleIndices[0] - i, middleIndices[-1] + i])
                         
                     colorH, outofBounds = colorMapping.interpolate(middleIndices[-1] + i)
                     
                     colorS, outofBounds = saturationMapping.interpolate(middleIndices[-1] + i)
                     colorV, outofBounds = valueMapping.interpolate(middleIndices[-1] + i)
                     
                     
                     print("colorH: {}".format(colorH))
                     
                     # S and V values are not important at initialization stage, 
                     # because they will be assigned during animation
                    
                     fieldColorDeque.append(ColorHSV(colorH, colorS, colorV))
                     #fieldColorDeque.append(ColorHSV(colorH, fieldColor[0].S, fieldColor[0].V ))
             # one color for each field
             else :
                # print(tuple(middleIndices))
                 fieldLEDIndexList.append(tuple(middleIndices))
                 fieldLEDIndexList.extend(list(
                                               zip(
                                                   range(middleIndices[0] - 1, middleIndices[0] - numberOfSideIndices, -1),
                                                   range(middleIndices[-1] + 1, middleIndices[-1] + numberOfSideIndices))))
                 #print(fieldLEDIndexList)    
                 fieldColorDeque.extend([fieldColor[0] for j in range(numberOfSideIndices)])
                 #print(fieldColorDeque)
            
             # flip order of LED indices if lights should go from inside to outside
             if not self.outin :
                 fieldLEDIndexList = fieldLEDIndexList[::-1]
                 
             self.allFieldsAllColors.append([fieldLEDIndexList, fieldColorDeque])
    
        
            
    
    def printColors(self):
        pprint(self.allFieldsAllColors)
        for dicdic in self.allFieldsAllColors:
                for i in range(len(dicdic[0])):
                    pprint("LED indices: {}".format(dicdic[0][i]))
                  #  pprint(dicdic[1])
                    print("Color(H:{0}, S:{1}, V:{2})".format(
                            #     dicdic[1][i],
                                 dicdic[1][i].H,
                                 dicdic[1][i].S,
                                 dicdic[1][i].V))
    def getFirstTwoColors(self):
        return self.allFieldsAllColors[1][0], self.allFieldsAllColors[1][1]  
    
    # colorList must be the same length as fieldColorDeque
    def updateColorValues(self, colorValues, fieldIndex):
        
        fieldColorDeque = self.allFieldsAllColors[fieldIndex][1]
        
        for i in range(len(fieldColorDeque)) :
            fieldColorDeque[i].V = colorValues[i]
    
    def setAllValues(self, val):

        for dicdic in self.allFieldsAllColors:
            for i in range(len(dicdic[0])):
                colHSV = dicdic[1][i]
                dicdic[1][i] = ColorHSV(colHSV.H, colHSV.S, val)
                print dicdic[1][i].V
        
    def getLowerBoundColor(self):
        
        return self.allFieldsAllColors[1][0]
       
        #todo von innen die Indizes verteilen (geschieht aber eh ueber ...

# TODO         
 # class twoColorFieldsMiddle(object):
 #     def __init__(self, fields, fieldColors, fromMiddle = True):
 #         colorFields.__init__(self, fields)      

#TODO 
# class oneColorFieldsSide(object):
#     def __init__(self, fields, fieldColors, leftToRight = True):
# 
# class twoColorFieldsSide(object):
#     def __init__(self, fields, fieldColors, leftToRight = True):

#TODO l2rColorFields 

class fieldColorCycle(object):
    
    def __init__(self, pdlmsettings):
        
        self.fields = pdlmsettings.fields
        self.numFields = pdlmsettings.numFields
        self.timeSignature = pdlmsettings.timeSignature
        self.colorDICT = {
                          'RED':Color(255.0,0.0,0.0,1.0),
                          'GREEN':Color(0.0,255.0,0.0, 1.0),
                          'BLUE':Color(0.0,0.0,255.0, 1.0),
                          'WHITE':Color(255.0,255.0,255.0, 1.0)
                          }
        self.fieldList = list(list())
       # self.fieldCycle = cycle(self.fieldList)       
        self.colorList = list()
        #self.colorCycle = cycle(self.colorList)
        self.initializeFieldColorCycles()
        
        self.fcCycle = cycle(zip(self.fieldList, self.colorList))
     
    def initializeFieldColorCycles(self):
         
         # 4/4
         if self.timeSignature == TimeSignatures._4_4 :
            
             self.fieldList.append(list([self.fields[2]]))                    #1
             self.fieldList.append(list([self.fields[1], self.fields[3]]))    #2
             self.fieldList.append(list([self.fields[0], self.fields[4]]))    #3
             self.fieldList.append(list([self.fields[1], self.fields[3]]))    #4
             
             self.colorList.append(self.colorDICT['RED'])                 #1             
             self.colorList.append(self.colorDICT['WHITE'])               #2
             self.colorList.append(self.colorDICT['WHITE'])               #3
             self.colorList.append(self.colorDICT['WHITE'])               #4

         
         # 3/4    
         elif self.timeSignature == TimeSignatures._3_4 :
             
             self.fieldList.append(list([self.fields[2]]))                    #1
             self.fieldList.append(list([self.fields[1], self.fields[3]]))    #2
             self.fieldList.append(list([self.fields[0], self.fields[4]]))    #3
             
             self.colorList.append(self.colorDICT['RED'])                 #1
             self.colorList.append(self.colorDICT['WHITE'])               #2
             self.colorList.append(self.colorDICT['WHITE'])               #3
            
         
         # 6/8
         elif self.timeSignature == TimeSignatures._6_8 :
             
             self.fieldList.append(list([self.fields[2]]))                    #1
             self.fieldList.append(list([self.fields[1], self.fields[3]]))    #2
             self.fieldList.append(list([self.fields[0], self.fields[4]]))    #3
             self.fieldList.append(list([self.fields[2]]))                    #4
             self.fieldList.append(list([self.fields[1], self.fields[3]]))    #5
             self.fieldList.append(list([self.fields[0], self.fields[4]]))    #6
             
             self.colorList.append(self.colorDICT['RED'])                 #1
             self.colorList.append(self.colorDICT['WHITE'])               #2
             self.colorList.append(self.colorDICT['WHITE'])               #3
             self.colorList.append(self.colorDICT['BLUE'])                #4
             self.colorList.append(self.colorDICT['WHITE'])               #5
             self.colorList.append(self.colorDICT['WHITE'])               #6

         
         # 5/4
         elif self.timeSignature == TimeSignatures._5_4 :
             
             
             self.fieldList.append(list([self.fields[0]]))                    #5             
             self.fieldList.append(list([self.fields[1]]))                    #4
             self.fieldList.append(list([self.fields[2]]))                    #3             
             self.fieldList.append(list([self.fields[3]]))                    #2
             self.fieldList.append(list([self.fields[4]]))                    #1
             
             self.colorList.append(self.colorDICT['RED'])                 #1
             self.colorList.append(self.colorDICT['WHITE'])               #2
             self.colorList.append(self.colorDICT['WHITE'])               #3
             self.colorList.append(self.colorDICT['BLUE'])                #4
             self.colorList.append(self.colorDICT['WHITE'])               #5
             
             
             
         else : 
             print "dayum"
         


"""
 
lgap = [10,2,8,2,8,2,8,2,10]
 
settings = pdlmSettings(lgap)
 
fieldColors = [[ColorHSV(0.01,0.0,0.0),ColorHSV(222,0.0,0.0)], 
               [ColorHSV(0.01,0.0,0.0),ColorHSV(222,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0),ColorHSV(222,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0),ColorHSV(222,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0),ColorHSV(222,0.0,0.0)]]

fieldColors = [[ColorHSV(0.01,0.0,0.0)], 
               [ColorHSV(0.01,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0)],
               [ColorHSV(0.01,0.0,0.0)]]
hm  = colorFieldsMiddle(settings, True)
hm.printColors()

 
yaxbObj = yaxb(minX = 1, midX = 4, maxX = 10, minY = 40, maxY = 70, n = 5)
yaxb

"""

 



lgap = [10,2,8,2,8,2,8,2,10]

fieldsl2r = leftRightFields(lgap, True)
# 
# midFields = middleFields(lgap, True)
# midFields.printColors()
# midFields.printColorPairs()
# 
# for i in lgap :
#     print i

# for i in range(13):
#     lgap.shiftUp(ColorHSV(3,1,1))
#     if (i > 7) : 
#         print("--------------------------------------------------------------------------------")
#         print("{0}  {0}  {0}  {0}  {0}  {0}  {0}  {0}  {0}  {0}  {0}  ".format(i))
#         lgap.printColorPairs()
# 
# 
# for i in range(len(lgap.ledIndexList)):
#     if lgap.ledIndexList[i] is not None :
#         for iLED in lgap.ledIndexList[i] :
#             print("{0} , {1}".format(iLED, lgap.colorDeque[i].getColorRGB()))




# for i in range(5):
#     lgap.shiftUp(ColorHSV(i,1,1))
#     
# lgap.printColorPairs()
