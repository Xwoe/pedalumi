from lpd8806.LPD8806 import *
from pdlmUtils import rangeDict
from pdlmEnums import Animations, TimeSignatures
from pprint import pprint
from collections import deque
import pyaudio, struct
from aubio.task import *
 
class pdlmSettings(object):
    def __init__(self,
                 ledsAndGaps,
                 animationType = Animations.LINEAR_L2R, 
                 numLEDs = 0,
                 startIndex = 0,
                 endIndex = 0,
                 #settings for the H in ColorHSV
                 minMidiNote = 40,               #guitar standard tuning: 40 | bass standard tuning: 28
                 maxMidiNote = 90,               #guitar ~86
                 minColorH = 0.0,            #HSV Range                
                 maxColorH = 360.0,
                 # settings for the S in ColorHSV
                 minSaturationEnergy = 1e15, 
                 maxSaturationEnergy = 1e17,
                 minSaturation = 0.5,
                 maxSaturation = 1.0,
                 # settings for the V in ColorHSV
                 minValueEnergy = 1e15,
                 maxValueEnergy = 1e17,
                 minValue = 0.0,
                 maxValue = 1.0,
                 updateInterval = 0.01,
                 tunerUpdateInterval = 0.05,
                 bpm = 90, 
                 fieldColors = None, # for spectrum analyzer list(list(Color)) the innerlist having at most two colors
                 reverseLEDorder = False,
                 fullScale = True,          # True: colors are mapped to the full min / maxMidinote Range 
                 fullNotes = True,          # if Noterange is just the 12 tones, fullNotes determines if 
                                            # the colors should be rounded to the integer Part of the 
                                            # Midinote
                 minFreqIntensity = 4.0,
                 midFreqIntensity = 7.0,
                 maxFreqIntensity = 10.0,
                 orderFieldLEDsOutIn = False,
                 timeSignature = TimeSignatures._4_4,
                 correctTuning = 0.05,
                 channels=1,
                 specinformat=pyaudio.paFloat32,
                 aubioinformat=pyaudio.paInt16,
                 rate=32000,
                 framesize=4096,
                 aubiopitchalg=aubio_pitch_fcomb):        #aubio_pitch_yinfft                              
        
        #################################
        # Audio Settings
        #################################
        self.channels = channels
        self.specinformat = pyaudio.paFloat32
        self.aubioinformat = pyaudio.paInt16
        self.aubiopitchalg = aubiopitchalg
        self.rate = rate
        self.framesize = framesize
        
        
        #################################
        # global settings
        #################################
        
        self.ledsAndGaps = ledsAndGaps
        
        if numLEDs == 0:
            self.numLEDs = sum(x for x in ledsAndGaps[0::2])
        else :
            self.numLEDs = numLEDs
        
        self.fields = []
        self.setFields()
        self.numFields = len(self.fields)
        
        self.multiColorDict = dict()
        self.twoColorDict = dict()
        self.singleColorDict = dict()
        self.setColorDicts()
        
        self.tonalRangeDict = dict()
        self.setTonalRangeDict()
        
        
        # if true the minimum LED index starts from the right
        self.reverseLEDorder = reverseLEDorder
            
        # controls the saturation in the Animations    
        self.minSaturationEnergy = minSaturationEnergy  
        self.maxSaturationEnergy = maxSaturationEnergy 
        self.minSaturation = minSaturation
        self.maxSaturation = maxSaturation
        
        # controls the Values (intensity) in the Animations
        self.minValueEnergy = minValueEnergy 
        self.maxValueEnergy = maxValueEnergy 
        self.minValue = minValue 
        self.maxValue = maxValue 
        
        #################################
        # settings for tuner
        #################################
        self.correctTuning = correctTuning   
        self.startIndex = startIndex
        if endIndex == 0 : 
            self.endIndex = numLEDs - 1
        else: 
            self.endIndex = endIndex
        
        #################################
        # Animation settings
        #################################
        self.animationType = animationType    
        self.minMidiNote = minMidiNote  # whole range settings     (e.g. absolute lowest tone of guitar / bass scale)
        self.maxMidiNote = maxMidiNote  #                        (e.g. absolute maximum Note of your guitar / bass)
        self.minColorH = minColorH        # which color to display for the lowest note
        self.maxColorH = maxColorH        # which color to display for the highest note
        
        self.updateInterval = updateInterval  
        self.tunerUpdateInterval = tunerUpdateInterval

        self.fullScale = fullScale # use the full scale of your instrument determined by min/maxMidiNote
        self.fullNotes = fullNotes # should note values be rounded or not
        

        
        #################################
        # settings for spectrum analysis
        #################################
        self.minFreqIntensity = minFreqIntensity
        self.midFreqIntensity = midFreqIntensity
        self.maxFreqIntensity = maxFreqIntensity
        self.orderFieldLEDsOutIn = orderFieldLEDsOutIn
        
        if fieldColors is not None :
            #self.minValueH and self.maxValueH will be overwritten!  
            self.setFieldColors(fieldColors)
        else :    
            self.fieldColors = fieldColors
        
        #################################
        # settings for metronome
        #################################
        
        # also the fieldColors
        self.bpm = bpm
        self.timeSignature = timeSignature
        

    def setUpdateInterval(self, interval):
        self.updateInterval = interval
    
    def setMaxBrightness(self, brightness):           
        
        if brightness > 1.0 : 
            self.maxValue = 1.0
        elif brightness < 0.1 : 
            self.maxValue = 0.1 
            
        else :
            self.maxValue = brightness
        
    # generate ranges from the ledsAndGaps list
    def setFields(self):
       
        ledIndex = 0
        for field in self.ledsAndGaps[0::2] :
            upperIndex = ledIndex + field 
            self.fields.append(range(ledIndex, upperIndex))
            ledIndex = ledIndex + field 
      #  pprint(self.fields)
    
  #  def setFieldColorDict(self):
        
        
    
    def printSettings(self):
        pprint("ledsAndGaps: {}".format(self.ledsAndGaps))
        pprint("animationType: {}".format(self.animationType))
        pprint("numLEDs: {}".format(self.numLEDs))
        pprint("minMidiNote: {}".format(self.minMidiNote))
        pprint("maxMidiNote: {}".format(self.maxMidiNote))
        pprint("minColorH: {}".format(self.minColorH))
        pprint("maxColorH: {}".format(self.maxColorH))
        pprint("minSaturationEnergy: {}".format(self.minSaturationEnergy))
        pprint("maxSaturationEnergy: {}".format(self.maxSaturationEnergy))
        pprint("minSaturation: {}".format(self.minSaturation))
        pprint("maxSaturation: {}".format(self.maxSaturation))
        
        pprint("minValueEnergy: {}".format(self.minValueEnergy))
        pprint("maxValueEnergy: {}".format(self.maxValueEnergy))
        pprint("minValue: {}".format(self.minValue))
        pprint("maxValue: {}".format(self.maxValue))
        
        pprint("updateInterval: {}".format(self.updateInterval))
        pprint("reverseLEDorder: {}".format(self.reverseLEDorder))
        
        pprint("fullScale: {}".format(self.fullScale))
        pprint("fullNotes: {}".format(self.fullNotes))
        
        
    def setColorDicts(self):
        
        ###########################
        # single color
        ###########################
        
        self.singleColorDict['RED'] = self.getFieldColorList(0.0, 0.0)
        self.singleColorDict['ORANGE'] = self.getFieldColorList(30.0, 30.0)
        self.singleColorDict['YELLOW'] = self.getFieldColorList(60.0, 60.0)
        self.singleColorDict['GREEN'] = self.getFieldColorList(120.0, 120.0)
        self.singleColorDict['CYAN'] = self.getFieldColorList(180.0, 180.0)
        self.singleColorDict['BLUE'] = self.getFieldColorList(240.0, 240.0)
        self.singleColorDict['PINK'] = self.getFieldColorList(300.0, 300.0) 
        
        ###########################
        # two colors
        ###########################
        self.twoColorDict['FULLRANGE'] = self.getFieldColorList(0.0, 360.0)
        self.twoColorDict['BLUE_TO_GREEN'] = self.getFieldColorList(240.0, 120.0)
        self.twoColorDict['BLUE_TO_RED'] = self.getFieldColorList(240.0, 360.0)
        self.twoColorDict['CYAN_GREEN_RED'] = self.getFieldColorList(180.0, 360.0)
        self.twoColorDict['CYAN_BLUE_RED'] = self.getFieldColorList(180.0, 0.0)
        self.twoColorDict['GREEN_TO_RED'] = self.getFieldColorList(120.0, 360.0)
        self.twoColorDict['YELLOW_TO_RED'] = self.getFieldColorList(60.0, 0.0)
        self.twoColorDict['ORANGE_TO_RED'] = self.getFieldColorList(30.0, 0.0)    
        
        ###########################
        # different colors
        ###########################

        self.multiColorDict['1_FULLRANGE'] = self.getMultiFieldColorList(0.0, 360.0)
        self.multiColorDict['2_FULLRANGE'] = self.getMultiFieldColorList(0.0, 360.0, False)
        self.multiColorDict['1_RED_TO_GREEN'] = self.getMultiFieldColorList(0.0, 150.0)
        self.multiColorDict['2_RED_TO_GREEN'] = self.getMultiFieldColorList(0.0, 150.0, False)
        self.multiColorDict['1_GREEN_TO_PINK'] = self.getMultiFieldColorList(120.0, 300.0)
        self.multiColorDict['2_GREEN_TO_PINK'] = self.getMultiFieldColorList(120.0, 300.0, False)
        self.multiColorDict['1_CYAN_TO_RED'] = self.getMultiFieldColorList(180.0, 360.0)
        self.multiColorDict['2_CYAN_TO_RED'] = self.getMultiFieldColorList(180.0, 360.0, False)
        
    
        
    
    # sets the fieldColors to this single color 
    def setFieldColor(self, colorHSV):
        
        self.fieldColors = self.getFieldColorHSV(colorHSV, colorHSV)
        self.minColorH = colorHSV.H
        self.maxColorH = colorHSV.H
        
        print "setFieldColor minColorH = {0}, maxColorH = {1}".format(self.minColorH, self.maxColorH)
    
    # sets the fieldColors to these two colors    
    def setTwoFieldColors(self, colorHSV1, colorHSV2):
        
        self.fieldColors = self.getFieldColorHSV(colorHSV1, colorHSV2)
        self.minColorH = colorHSV1.H
        self.maxColorH = colorHSV2.H
        
        print "setTwoFieldColors minColorH = {0}, maxColorH = {1}".format(self.minColorH, self.maxColorH)
    
    # assigns the list (e.g. from twoColorDict) to fieldColors
    def setFieldColors(self, fieldColorList):
        
        self.fieldColors = fieldColorList    
        
        pprint(fieldColorList)
        # simply take the first field for the min / max H value
        self.minColorH = self.fieldColors[0][0].H
        self.maxColorH = self.fieldColors[-1][1].H
        
        print "setFieldColors minColorH = {0}, maxColorH = {1}".format(self.minColorH, self.maxColorH)
        
     
    def setTonalRangeDict(self):
        
        self.tonalRangeDict['Guitar Standard'] = (40, 90)
        self.tonalRangeDict['Guitar C'] = (36, 86)
        self.tonalRangeDict['Guitar D'] = (38, 88)
        self.tonalRangeDict['Bass Standard'] = (28, 66)
    
    def setTonalRange(self, twoTones):
        
        self.minMidiNote = twoTones[0]
        self.maxMidiNote = twoTones[1]
    
    # write the two color H values into a colorfield array and return them   
    def getFieldColorList(self, colorH1, colorH2):
        
        colField = []
        for i in range(self.numFields) :
            colField.append([ColorHSV(colorH1,1.0,1.0),ColorHSV(colorH2,1.0,1.0)])

        return colField
    
    
    # assigns the colors to the Fields, interpolating from colorH1 to colorH1
    # if discrete = True one value per field is used, if false values are interpolated
    def getMultiFieldColorList(self, colorH1, colorH2, discrete = True):
        colField = []
        
        if discrete :
            
            # e.g. if you have 5 fields and want to have colors ranging from 0 - 150
            # you have to divide by 4 to get a delta of 37.5 -> 0 | 37.5 | 75 | 112.5 | 150 
            delta = float(colorH2 - colorH1) / float(self.numFields - 1) 
            for i in range(self.numFields) :
                val = colorH1 + i * delta
                colField.append([ColorHSV(val,1.0,1.0),ColorHSV(val,1.0,1.0)])
                
        else : 
            delta = float(colorH2 - colorH1) / float(self.numFields)
            for i in range(self.numFields) :
                val1 = colorH1 + i * delta
                val2 = colorH1 + (i+1) * delta
                colField.append([ColorHSV(val1,1.0,1.0),ColorHSV(val2,1.0,1.0)])
        
        return colField       
     
    # write the two colors into a colorfield array and return them
    def getFieldColorHSV(self, colorHSV1, colorHSV2):
        
        colField = []
        for i in range(self.numFields) :
            colField.append([colorHSV1, colorHSV2])

        return colField    

    def printColorFields(self):
        
        pprint(self.fieldColors)
        pprint("singleColorDict".format(self.singleColorDict))
        pprint("twoColorDict".format(self.twoColorDict))
        
        for i in range(len(self.fieldColors)) :
            print("Color1 (H:{0}, S:{1}, V:{2})".format(
                                 self.fieldColors[i][0].H,
                                 self.fieldColors[i][0].S,
                                 self.fieldColors[i][0].V))

            print("Color2 (H:{0}, S:{1}, V:{2})".format(
                                 self.fieldColors[i][1].H,
                                 self.fieldColors[i][1].S,
                                 self.fieldColors[i][1].V))
        




NUMLEDS = 44
ANIM = Animations.LINEAR_L2R
REVERSELEDORDER = True
UPDATEINTERVAL = 0.05
 
MINMIDINOTE = 40
MAXMIDINOTE = 86
 
MINCOLOR = 0.0
MAXCOLOR = 360.00
 
 
LEDSANDGAPS = (10,2,8,2,8,2,8,2,10)
 
settings = pdlmSettings(LEDSANDGAPS,
                        ANIM, 
                        minMidiNote = MINMIDINOTE,
                        maxMidiNote = MAXMIDINOTE,
                        minColorH = MINCOLOR,
                        maxColorH = MAXCOLOR,
                        updateInterval = UPDATEINTERVAL, 
                        reverseLEDorder = True,
                        fullScale = True,
                        fullNotes = True) 


