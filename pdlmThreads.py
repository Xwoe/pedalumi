from lpd8806.LPD8806 import *
import threading
import pdlmUtils
import time
import pdlmAubio
import copy
import numpy as np
from time import sleep
from pdlmEnums import Animations
from pdlmEnums import TimeSignatures
from pdlmLEDDict import *
from midiNoteMap import *
from pdlmSettings import pdlmSettings
from itertools import islice, cycle


# this is more of an abstract class, don't instatiate this
class pdlmThread(threading.Thread):
    
    def __init__(self, pdlmsettings):
        type(self).numLEDs = pdlmsettings.numLEDs
        threading.Thread.__init__(self)
        self.daemon = True
        self.led = LEDStrip(self.numLEDs)
        self.aubioThread = pdlmAubio.aubioThread(pdlmsettings)
        self._stop = threading.Event()
        self.updateInterval = pdlmsettings.updateInterval
        """
        self.colorDICT = {
                          'RED':(255.0,0.0,0.0),
                          'GREEN':(0.0,255.0,0.0),
                          'BLUE':(0.0,0.0,255.0),
                          'WHITE':(255.0,255.0,255.0)
                          }
        """
        self.colorDICT = {
                          'RED':Color(255.0,0.0,0.0,1.0),
                          'GREEN':Color(0.0,255.0,0.0, 1.0),
                          'BLUE':Color(0.0,0.0,255.0, 1.0),
                          'WHITE':Color(255.0,255.0,255.0, 1.0)
                          }
        self.initialized = False
        
    def stop(self):
        self._stop.set()
        
    def stopped(self):
        return self._stop.isSet()
    
    def isInitialized(self):
        return self.initialized
   
    def updateLights(self):
        return None
        
        
class pdlmTuner(pdlmThread):
     def __init__(self, pdlmsettings):
         pdlmThread.__init__(self, pdlmsettings)
        # self.numLEDs = numLEDs
         self.aubioThread = pdlmAubio.aubioThread(pdlmsettings, flagENERGY = False, flagPITCH = True)
         # the indices determine the range where the tuning should be displayed
         # e.g. you have 50 LEDs and want to display the tuner in the middle 10 LEDs
         # you would set startIndex = 45 and endIndex = 55

        #positiveFields is a list of ranges with LED indices. These indexranges lighten up, when the tuning is correct.
         
         if pdlmsettings.updateInterval < 0.0 :
             raise ValueError('updateInterval must be greater 0.0') 
         
         self.startIndex = pdlmsettings.startIndex
         self.endIndex = pdlmsettings.endIndex
         self.positiveFields = pdlmsettings.fields[0], pdlmsettings.fields[-1]

         self.reversed = pdlmsettings.reverseLEDorder
         print "startIndex {}".format(self.startIndex)
         print "endIndex {}".format(self.endIndex)
         
         self.pitchDict = pdlmUtils.rangeDict(self.startIndex, self.endIndex, -0.5, 0.5)
         
         # LED settings
         # Get the indices for the middle LEDs and all the LEDs which are used for tuning
         
         self.middle = pdlmUtils.determineMiddleIndices(self.startIndex, self.endIndex)
         print(self.middle)
         self.updateInterval = pdlmsettings.tunerUpdateInterval
         self.curStartPixel = 0
         self.curEndPixel = 0
         self.curOffset = 0.0
         self.curMidinote = "A-0"

         self.correctTuning = 0.05
         
         self.brightness = pdlmsettings.maxValue
       #  self.led = LEDStrip(self.numLEDs)
         self.led.all_off()
         

     def run(self):
     
        #initialize Aubio thread to get the pitch
        print "about to start"
        self.aubioThread.daemon = True  #this way the thread will stop when the main thread is aborted
        self.aubioThread.start()
        print "started"
 
        elapsed = 0.0
       # while runflag:
        while not self._stop.isSet(): # and elapsed < 20 :
            
            start = time.time()
            try:
    
                # get the current offset and midinote from the Aubio thread
                self.curOffset = self.aubioThread.curOFFSET
                self.curMidinote = self.aubioThread.curMIDINOTE
                
                print "{0}, {1}".format(self.curMidinote, self.curOffset) 
            
                # lighten up LEDs 
                try: 
                    self.updateLights(self.curOffset)
                except Exception as ex:
                    print "sth went wrong with updateLights: {}".format(ex)    
                # update LCD display
    
            except Exception as e:
                print "Just a lil Ex in pitch: {}".format(e)
            
            sleep(self.updateInterval)
            elapsed = elapsed + (time.time() - start)
                
            self.initialized = True

           
        self.led.all_off()    
     
        print "pdlm Loop stopped, shutting down aubioThread"
        
        self.aubioThread.stop()
        self.aubioThread.join()
        print "pdlm Loop stopped, shutting down aubioThread"
        
     def updateLights(self, curoffset):
 
        brightness = 0.5
        startPixel = endPixel = self.pitchDict.getRangeIndex(curoffset, self.reversed)
        print "pixelnumber = {}".format(startPixel)
       # print "{0}, {1}".format(curmidinote, curoffset)
       
        #r, g, b = self.colorDICT['RED']
        col = self.colorDICT['RED']
        col = Color(col.R, col.G, col.B, self.brightness)
        
        correctTuning = False
        
        # pitch seems to be quite correct
        if self.middle[0] <= startPixel <= self.middle[-1]:
            #r, g, b = self.colorDICT['GREEN']
            col = self.colorDICT['GREEN']
            col = Color(col.R, col.G, col.B, self.brightness)
        
            #pitch seems to be perfect
            if abs(curoffset) < self.correctTuning :
                startPixel = self.middle[0]
                endPixel = self.middle[-1]
                correctTuning = True
                print("correctTuning")
       
       # check if something has changed compared to the last round -> less flickering
        if not ((self.curStartPixel == startPixel) and (self.curEndPixel == endPixel)) :
            
            self.curStartPixel = startPixel
            self.curEndPixel = endPixel
            # always all_off before anything else is done, otherwise the indeces get mixed up
            self.led.all_off()
            
            self.led.fill(col, startPixel, endPixel)  
            if correctTuning :    
                for positiveRange in self.positiveFields :
                    self.led.fill(col, positiveRange[0], positiveRange[-1])
                    print("posR0: {0}, posR1: {1}".format(positiveRange[0], positiveRange[-1]))
                    
                 
            self.led.update()



class pdlmAnimation(pdlmThread):
     def __init__(self, pdlmsettings):
        pdlmThread.__init__(self, pdlmsettings)

        self.ledsAndGaps = pdlmsettings.ledsAndGaps
        self.animationType = pdlmsettings.animationType
        self.minMidiNote = pdlmsettings.minMidiNote
        self.maxMidiNote = pdlmsettings.maxMidiNote
        print "minMidiNote {}".format(self.minMidiNote)
        print "maxMidiNote {}".format(self.maxMidiNote)
        
        self.minColorH = pdlmsettings.minColorH
        self.maxColorH = pdlmsettings.maxColorH
        self.updateInterval = pdlmsettings.updateInterval  
        self.reverseLEDorder = pdlmsettings.reverseLEDorder
        self.fullScale = pdlmsettings.fullScale
        self.fullNotes = pdlmsettings.fullNotes
        
        self.minValueEnergy = pdlmsettings.minValueEnergy
        self.maxValueEnergy = pdlmsettings.maxValueEnergy
        self.minValue = pdlmsettings.minValue
        self.maxValue = pdlmsettings.maxValue

               
        self.minSaturationEnergy = pdlmsettings.minSaturationEnergy  
        self.maxSaturationEnergy = pdlmsettings.maxSaturationEnergy 
        self.minSaturation = pdlmsettings.minSaturation
        self.maxSaturation = pdlmsettings.maxSaturation

        
        # dynamic values
        self.lastColor = ColorHSV(0.0,0.0,0.0)
        self.curMidiFloat = 0.0
        self.curEnergy = 0 
        
        # Dictionaries
        self.ledDict = ledDict(self.ledsAndGaps)      
        self.colorRangeDict = None
        self.valueDict = pdlmUtils.linearInterpolation(self.minValueEnergy, 
                                                       self.maxValueEnergy, 
                                                       self.minValue, 
                                                       self.maxValue)
        
        self.saturationDict = pdlmUtils.linearInterpolation(self.minSaturationEnergy,
                                                            self.maxSaturationEnergy,                                                            
                                                            self.minSaturation,
                                                            self.maxSaturation)
        
        if(self.fullScale):
            self.colorRangeDict = pdlmUtils.linearInterpolation(self.minMidiNote, self.maxMidiNote ,self.minColorH, self.maxColorH)
            
        else :
            self.colorRangeDict = pdlmUtils.linearInterpolation(1, 12, self.minColorH, self.maxColorH)
        
        print "[Animthread] setFieldColors minColorH = {0}, maxColorH = {1}".format(self.minColorH, self.maxColorH)
                
        self.aubioThread = pdlmAubio.aubioThread(pdlmsettings, flagENERGY = True, flagPITCH = False, flagANIM = True)
      
      # /!\ Achtung geaendert
      #  self.runAnimation()
        
         
        
        
    
      
          # /!\ Achtung geaendert    
     def run(self):
       
       self.led.all_off()
       self.led.update()
       self.updateAnimationType()
       
       currentAnimation = self.animationType
       
       #loop
       
       #initialize Aubio thread to get the pitch
       print "Aubio about to start"
       self.aubioThread.daemon = True  #this way the thread will stop when the main thread is aborted
       self.aubioThread.start()
       print "Aubio started"

       elapsed = 0.0
      # while runflag:
       while not self._stop.isSet(): # and elapsed < 20 :
           
           try :
               start = time.time()
               self.curMidiFloat = self.aubioThread.curMIDIFLOAT
               self.curEnergy = self.aubioThread.curENERGY
               self.updateLights()
            
           
               sleep(self.updateInterval)
               elapsed = elapsed + (time.time() - start)
                   
               self.initialized = True
           except Exception as e:
               print "Just a lil Ex in animLoop: {}".format(e.message())
           
       self.led.all_off()    
     
       print "pdlm Loop stopped, shutting down aubioThread"
        
       self.aubioThread.stop()
       self.aubioThread.join()
       print "pdlm Loop stopped, shutting down aubioThread"
       
     def updateLights(self): 
        

        #determine current color
         try: 
            #TODO
            if(not self.fullScale) :
                midinote = getChromaticNumber(self.curMidiFloat, self.fullNotes)
            
            newColor =  ColorHSV(self.minColorH,1.0,1.0)
            
            lowenergy = self.curEnergy < self.minValueEnergy
            
            #TODO: support multiple color fields for animation
            # first check, if fields have different colors
            
            colorH, outOfBounds = self.colorRangeDict.interpolate(self.curMidiFloat)
            colorS, sOutOfBounds  = self.saturationDict.interpolate(self.curEnergy)
            colorV, vOutOfBounds = self.valueDict.interpolate(self.curEnergy)
            
            
            # set the flag if errors in pitch detection should be treated
            checkoutOfBounds = False
            
            if checkoutOfBounds : 
                if outOfBounds:
                     print("before newColor Hue {}".format(newColor.H))
                     print("before lastColor Hue {}".format(self.lastColor.H))
                     newColor = self.lastColor#copy.deepcopy(self.lastColor)
                     print("************************************out of bounds, colorH: {0} using lastColor H: {1}".format(colorH, self.lastColor.H))
                     print("after newColor Hue {}".format(newColor.H))
                     print("after lastColor Hue {}".format(self.lastColor.H))
                
                # if pitch is out of bounds it might as well be that no sound is heard
                # so keep the last H / S , but set the new V
                elif lowenergy: 
                    
                    newColor.V = colorV
                
                else :
                    print("before newColor Hue {}".format(newColor.H))
                    print("before lastColor Hue {}".format(self.lastColor.H))
                    newColor = ColorHSV(colorH, colorS, colorV)
                    self.lastColor = newColor 
                    print("after newColor Hue {}".format(newColor.H))
                    print("after lastColor Hue {}".format(self.lastColor.H))
            
            else :        
                 newColor = ColorHSV(colorH, colorS, colorV)
                 self.lastColor = newColor 
                 
                 print "colorH = {}".format(colorH)
                 if outOfBounds: 
                     print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~out of bounds, but I don't care")
#             print("newColor Hue {}".format(newColor.H))
#             print("lastColor Hue {}".format(lastColor.H))
            
            
            self.ledDict.shiftUp(newColor)
            self.setColors()
            self.led.update()
          #  print("sleep for {}s".format(self.updateInterval))
            sleep(self.updateInterval)
            
         except Exception as e:
             print("Error in updateLights: {}".format(e.message()))
        

     def setColors(self):
        for i in range(len(self.ledDict.ledIndexList)):
            if self.ledDict.ledIndexList[i] is not None :
                 for iLED in self.ledDict.ledIndexList[i] :
                    self.led.set(iLED, self.ledDict.colorDeque[i].getColorRGB())
         
    
            
     def setAnimation(self, animType):
        
        self.animationType = animType
        self.updateAnimationType()
    
     def updateAnimationType(self):   
                #check which animation type
        if self.animationType == Animations.LINEAR_L2R :
            print(Animations.LINEAR_L2R)
            self.ledDict = linear(self.ledsAndGaps, self.reverseLEDorder)
       
        elif self.animationType == Animations.LINEAR_R2L :
            print(Animations.LINEAR_R2L)
            self.ledDict = linear(self.ledsAndGaps, not self.reverseLEDorder)
        
        
        elif self.animationType == Animations.MIDDLE_ALL_FROM_MIDDLE :
            print(Animations.MIDDLE_ALL_FROM_MIDDLE)
            self.ledDict = middleAltogether(self.ledsAndGaps, True)
        
        
        elif self.animationType == Animations.MIDDLE_ALL_TO_MIDDLE :
            print(Animations.MIDDLE_ALL_TO_MIDDLE)
            self.ledDict = middleAltogether(self.ledsAndGaps, False)
            
        
        elif self.animationType == Animations.FIELDS_FROM_MIDDLE :
            print(Animations.FIELDS_FROM_MIDDLE)
            self.ledDict = middleFields(self.ledsAndGaps, True)
            
            
        elif self.animationType == Animations.FIELDS_TO_MIDDLE :
            print(Animations.FIELDS_TO_MIDDLE)
            self.ledDict = middleFields(self.ledsAndGaps, False)
        
        elif self.animationType == Animations.FIELDS_L2R :
            print(Animations.FIELDS_L2R)
            self.ledDict = leftRightFields(self.ledsAndGaps, self.reverseLEDorder)
            
        elif self.animationType == Animations.FIELDS_R2L :
            print(Animations.FIELDS_R2L)
            self.ledDict = leftRightFields(self.ledsAndGaps, not self.reverseLEDorder)
            
        else :
            print("what the what?")

class pdlmSpectrumAnalyzer(pdlmThread):
     def __init__(self, pdlmsettings):
        pdlmThread.__init__(self, pdlmsettings)  
        self.numFields = pdlmsettings.numFields
        
        self.minFreqIntensity = pdlmsettings.minFreqIntensity
        self.midFreqIntensity = pdlmsettings.midFreqIntensity
        self.maxFreqIntensity = pdlmsettings.maxFreqIntensity
        
        self.updateInterval = pdlmsettings.updateInterval
        
        self.colorFieldDict = colorFieldsMiddle(pdlmsettings)        
        self.yaxbFieldList = []
        self.initiateYaxbs(pdlmsettings)
        
        self.specthread = pdlmAubio.specThread(pdlmsettings)
       

         
     def initiateYaxbs(self, pdlmsettings):
        
        #iterate over all colorDeques and create yaxb Fields for them.
        # these are used to calculate the interpolation for the 
        for fieldAndColor in self.colorFieldDict.allFieldsAllColors : 
            fieldColorDeque = fieldAndColor[1]
            yaxbfield = pdlmUtils.yaxbField(pdlmsettings.minFreqIntensity,
                                            pdlmsettings.midFreqIntensity,
                                            pdlmsettings.maxFreqIntensity,
                                            0.0, 1.0, 
                                            len(fieldColorDeque))
            self.yaxbFieldList.append(yaxbfield)     
              
     def run(self):
        self.led.all_off()
        self.led.update()
        print "EQ Aubio about to start"
        self.specthread.daemon = True  #this way the thread will stop when the main thread is aborted
        self.specthread.start()
        print "EQ Aubio started"
         

        elapsed = 0.0
      # while runflag:
        while not self._stop.isSet(): # and elapsed < 20 :
            try:
                start = time.time()
                """
                self.curMidiFloat = self.aubioThread.curMIDIFLOAT
                self.curEnergy = self.aubioThread.curENERGY
                """
                self.updateLights()
                
                
                # sleep(self.updateInterval)
                elapsed = (time.time() - start)
                print("~~~~~~~~~~~~~ elapsedTime = {}".format(elapsed))  
                sleep(self.updateInterval / 10)
                self.initialized = True
            except Exception as e:
               print "Just a lil Ex in animLoop: {}".format(e.message())
           
        self.led.all_off()    
        self.specthread.stop()
        self.specthread.join()
        
     def updateLights(self):
        
        # get the current matrix of the power values for each frequency band
        freqMatrix = self.specthread.matrix
        print("len(freqMatrix) = {0}, len(yaxbFieldList) = {1}".format(len(freqMatrix), len(self.yaxbFieldList)))
        #iterate over the frequency power values and interpolate the values in each field
        for i in range(len(freqMatrix)) : 
            
            bandPower = freqMatrix[i]
            colorValues = self.yaxbFieldList[i].interpolate(bandPower)
        #    print("bandPower = {0}".format(bandPower))
         #   pprint("colorValues: {}".format(hueValues))
            
            
            # write the colorHues into the appropriate Field
            self.colorFieldDict.updateColorValues(colorValues, i)
            
         
        
        self.setColors()
        self.led.update()
     #   self.colorFieldDict.printColors()
       # print("sleep for {}s".format(self.updateInterval))
           
    # iterate over all LED indices and their mapped colors and update them 
     def setColors(self):   
         for fieldLEDsAndDeque in self.colorFieldDict.allFieldsAllColors :
            
            ledIndices = fieldLEDsAndDeque[0]
            colorDeque = fieldLEDsAndDeque[1]
            
            for i in range(len(colorDeque)) :
                for iLED in ledIndices[i] :
                    self.led.set(iLED, colorDeque[i].getColorRGB())
        
        
class pdlmMetronome(pdlmThread):
     def __init__(self, pdlmsettings):
        pdlmThread.__init__(self, pdlmsettings)  
        self.numFields = pdlmsettings.numFields      
        self.bpm = pdlmsettings.bpm
        self.interval = float(60) / float(pdlmsettings.bpm)
        self.timeSignature = pdlmsettings.timeSignature
        self.fields = pdlmsettings.fields
        
        self.led.all_off()
        self.fieldColorCycle = fieldColorCycle(pdlmsettings)
        print "interval = {}".format(self.interval)

     def run(self):
         
         self.initialized = True         
         
         for fieldList, col in self.fieldColorCycle.fcCycle  :      
            
             print col
             self.updateLights(fieldList, col)
            
             if self._stop.isSet() :
                break
            
         self.led.all_off()    
     
         print "metronome stopped"
                    
     def updateLights(self, fieldList, col):
         
         self.led.all_off()
         for field in fieldList: 
             self.led.fill(col, field[0], field[-1])              
         self.led.update()
         sleep(self.interval)
        
     def setBPM(self, bpm):
         self.bpm = bpm
         self.interval = float(60) / float(bpm)
        
        
class pdlmFillAll(pdlmThread):      
    
     def __init__(self, pdlmsettings):
        pdlmThread.__init__(self, pdlmsettings)  
        self.numFields = pdlmsettings.numFields
        self.fields = pdlmsettings.fields
        self.colorFieldDict = colorFieldsMiddle(pdlmsettings)

        
        self.led.all_off()
        
     def run(self):
         
         self.initialized = True
         self.updateLights()
        
         while not self._stop.isSet() :     
            
             
             sleep(1)
            
                         
         self.led.all_off()    
     
         print "color fill off"
                    
     def updateLights(self):
         
         self.led.all_off()
         self.colorFieldDict.setAllValues(1.0)
         self.setColors()
         self.led.update()

     def setColors(self):   
         
         for fieldLEDsAndDeque in self.colorFieldDict.allFieldsAllColors :
            
            ledIndices = fieldLEDsAndDeque[0]
            colorDeque = fieldLEDsAndDeque[1]
            
            for i in range(len(colorDeque)) :
                for iLED in ledIndices[i] :
                    self.led.set(iLED, colorDeque[i].getColorRGB())    
     
     def getColorStrings(self):
         #todo
         print("todo")
         
         
        # can be used to change colors on the fly   
     def changeColors(self, colorFieldDict):
         self.colorFieldDict = colorFieldDict
         self.updateLights()
        
        
#TODO static animations         
         
        
        

