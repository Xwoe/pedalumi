import threading
from lcd.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate
from lpd8806.LPD8806 import ColorHSV
import xml.etree.ElementTree as ET
from time import sleep
from pdlmSettings import pdlmSettings
from lpd8806.LPD8806 import ColorHSV
from pdlmEnums import *
from math import trunc
import pdlmThreads

#width of display
WIDTH = 16
NUMLEDS = 44

############################
# PDLMSETTINGS
############################
#indices for tuner
REVERSELEDORDER = True
STARTINDEX = 33
ENDINDEX = 10 
LEDSANDGAPS = (10,2,8,2,8,2,8,2,10)

#MINCOLORH = 0
#MAXCOLORH = 360
MINMIDINOTE = 60
MAXMIDINOTE = 100

MINSATURATIONENERGY = 1e15
MAXSATURATIONENERGY = 1e17
MINSATURATION = 0.5
MAXSATURATION = 1.0

MINVALUEENERGY = 1e15
MAXVALUEENERGY = 1e17
MINVALUE = 0.0
MAXVALUE = 1.0

UPDATEINTERVAL = 0.01
TUNERUPDATEINTERVAL = 0.07

BPM = 90
"""
FIELDCOLORS = [[ColorHSV(120.0,1.0,0.0),ColorHSV(240.0,1.0,0.0)], 
               [ColorHSV(120.0,1.0,0.0),ColorHSV(240.0,1.0,0.0)],
               [ColorHSV(120.0,1.0,0.0),ColorHSV(240.0,1.0,0.0)],
               [ColorHSV(120.0,1.0,0.0),ColorHSV(240.0,1.0,0.0)],
               [ColorHSV(120.0,1.0,0.0),ColorHSV(240.0,1.0,0.0)]]
"""
FIELDCOLORS = [[ColorHSV(60.0,1.0,0.0),ColorHSV(0.0,1.0,0.0)], 
               [ColorHSV(60.0,1.0,0.0),ColorHSV(0.0,1.0,0.0)],
               [ColorHSV(60.0,1.0,0.0),ColorHSV(0.0,1.0,0.0)],
               [ColorHSV(60.0,1.0,0.0),ColorHSV(0.0,1.0,0.0)],
               [ColorHSV(60.0,1.0,0.0),ColorHSV(0.0,1.0,0.0)]]

REVERSELEDORDER = True
FULLSCALE = True 
FULLNOTES = True 
MINFREQINTENSITY = 4.0
MIDFREQINTENSITY = 7.0
MAXFREQINTENSITY = 12.0
ORDERFIELDLEDSOUTIN = False 

TIMESIGNATURE = TimeSignatures._4_4
CORRECTTUNING = 0.05                                  

#if true the COLOR will be adjusted to the whole MIN / MAXMIDINOTE spectrum
#if false it will be adjusted to the scale from C to B
FULLSCALE = True

TIMESIGNATURES = "4/4", "3/4", "6/4", "5/4"    



DOUBLEDASH = "--".center(WIDTH)

class pdlmLCDMenu(object):
    
    def __init__(self):
        
        #TODO 1: save all the settings as attributes
        #TODO 2: write the tree to an XML file to save settings
        
        # rootnode main settings
        self.root = ET.Element("root") 
        self.root.set('numleds', NUMLEDS)
        self.root.set('startindex', STARTINDEX)
        self.root.set('endindex', ENDINDEX)
        self.root.set('updateinterval', UPDATEINTERVAL)
        self.root.set('reverseledorder', REVERSELEDORDER) 
        self.root.set('ledsandgaps', LEDSANDGAPS)           
          
        #########################
        # tuner 
        #########################
        self.tuning = self.addSub(self.root, "Tuner", hasSub = False, startsThread = True)
        
        ######################### 
        # Animations root
        #########################
        self.animations = self.addSub(self.root, "Animations", hasSub = True)
          
        # linear
        self.linear = self.addSub(self.animations, "linear (all)", hasSub = True, startsThread = False)
        self.l2r = self.addSub(self.linear, "left to right", hasSub = False, startsThread = True)
        self.r2l = self.addSub(self.linear, "right to left", hasSub = False, startsThread = True)
        
        #from or to middle
        self.middleAll = self.addSub(self.animations, "middle all", hasSub = True, startsThread = False)
        self.toMiddle = self.addSub(self.middleAll, "all to middle", hasSub = False, startsThread = True)
        self.fromMiddle = self.addSub(self.middleAll, "all from middle", hasSub = False, startsThread = True)
        
        #fields
        self.fields = self.addSub(self.animations, "fields", hasSub = True, startsThread = False)
        self.fieldsl2r = self.addSub(self.fields, "fields l2r", hasSub = False, startsThread = True)
        self.fieldsr2l = self.addSub(self.fields, "fields r2l", hasSub = False, startsThread = True)
        
        self.fieldsFromMiddle = self.addSub(self.fields, "fields from mid", hasSub = False, startsThread = True)
        self.fieldsToMiddle = self.addSub(self.fields, "fields to mid", hasSub = False, startsThread = True)
        
        ######################### 
        # constant light (fill all)
        ######################### 
        self.constantLight = self.addSub(self.root, "Constant light", hasSub = False, startsThread = True)
         
        #########################
        # Spectral Analysis
        #########################
        self.spectral = self.addSub(self.root, "Spectral start", hasSub = False, startsThread = True)

        
        #########################
        # Metronome
        #########################
        self.metronome = self.addSub(self.root, "Metronome", True, False)
        self.metroStart = self.addSub(self.metronome, "start Metronome", False, True)
        self.metroTS = self.addSub(self.metronome, "Time Signature", False, True)
        
        #########################
        # Settings
        #########################
        self.settings = self.addSub(self.root, "Settings", True, False)
        
        #color settings
        self.setColors = self.addSub(self.settings, "Set Colors", hasSub = True, startsThread = False)
        self.singleColor =  self.addSub(self.setColors, "single color", startsThread = True)
        self.twoColors =  self.addSub(self.setColors, "two colors", startsThread = True)
        self.multiColor = self.addSub(self.setColors, "multi colors", startsThread = True)
        
        #update interval settings
        self.updateInverval = self.addSub(self.settings, "Update Interval", hasSub = False, startsThread = True)
        
        #max brightness settings
        self.maxBrightness = self.addSub(self.settings, "set Brightness", hasSub = False, startsThread = True)
    
        #########################
        # Shutdown
        #########################
        
        self.shutdown = self.addSub(self.root, "SHUTDOWN", hasSub = False, startsThread = True)
        
    
        # the tree structure doesn't support parent access from children, so 
        # a dictionary is used to map these relations
        self.parent_map = dict((c, p) for p in self.root.getiterator() for c in p)
        
    # format string for root items with submenus
    def withsub(self, text):
        return  ' ' + text.ljust(WIDTH - 2) + '>'
    
    # format string for root items without submenus
    def nosub(self, text):
        return '<' + text.ljust(WIDTH)
    
    # add Sub Element to tree and set formatted name
    def addSub(self, parent, name, hasSub = False, startsThread = False):
        sub = ET.SubElement(parent, name)

        
        if hasSub :
            sub.Text = self.withsub(name) 
        elif parent is not self.root :
            sub.Text = self.nosub(name)
        else :
            sub.Text = ' ' + name.ljust(WIDTH)
        
        sub.set('startsThread', 'yes' if startsThread else 'no')
        return sub   
    def getParentLevelElements(self, elems, selected):

        # to get the children of the top level, you have to first 
        # get the parent of the parent 
        # and then the parent parent's children o_O            
        parent = self.parent_map[elems[selected]]
        parentOfParent = self.parent_map[parent]
        elems = list(parentOfParent)
        return elems, elems.index(parent)  
        


class pdlmLCDthread(threading.Thread):
    
    def __init__(self):
        
        threading.Thread.__init__(self)
        self.daemon = True
        self.lcd = Adafruit_CharLCDPlate()
        self.menuobj = pdlmLCDMenu()
        self.pdlmThreadARR = []
        self._stop = threading.Event()
        self.lastMenuDisplayString = ""
        self.pdlmsettings = self.initializePdlmSettings()
        
    def run(self):

        root = self.menuobj.root      
        elems = list(root) 
        
        # selected is the index of the Element currently selected in the menu
        selected = 0
        prevSelected = selected
        prevElems = elems
        
        self.updateDisplay(elems, selected)
      
        while not self._stop.isSet(): 
            
            # listen to the buttons 
            if self.lcd.buttonPressed(self.lcd.UP):
                if selected > 0 :
                    selected -= 1
                    print "UP lcd run selected: {0}".format(selected)
                sleep(0.2)
                    
            elif self.lcd.buttonPressed(self.lcd.DOWN):
                
                if selected < len(elems) - 1 :
                    selected += 1
                    print "DOWN lcd run selected: {0}".format(selected)
                sleep(0.2)
                
            elif self.lcd.buttonPressed(self.lcd.LEFT):
                
                if self.menuobj.parent_map[elems[selected]] is root :
                    print "LEFT lcd run: top Menu!"
                    
                else :
                    
                    elems, selected = self.menuobj.getParentLevelElements(elems, selected)
                    
                    print "LEFT lcd run parent Elems: {0}, selected {1}".format(elems, selected)
                sleep(0.2)    
                        
            elif self.lcd.buttonPressed(self.lcd.RIGHT):
                #if you are not in the deepest depth of the tree
                if len(list(elems[selected])) > 0:
                       elems = list(elems[selected])#elems[0].getChildren()
                       selected = 0
                print "RIGHT lcd run selected: {0}".format(selected)
                sleep(0.2)
                
            # select button    
            elif self.lcd.buttonPressed(self.lcd.SELECT) :
                if elems[selected].get('startsThread') == 'yes' :
                    print "SELECT lcd run: thread will be started"
                    self.manageThreads(elems[selected])
                    
                else :
                    print "SELECT lcd run: no thread to start"
                
                sleep(0.2)
            
           
            if prevSelected != selected or elems != prevElems :  #prevElement != elems[selected] or 
                
                print "sth changed lcd run: currentElement: {}".format(elems[selected].tag)
                self.updateDisplay(elems, selected)
                prevElems = elems
                prevSelected = selected
                
        self.cleanUp()

        

    def cleanUp(self):
        self.lcd.clear()
        self.lcd.backlight(self.lcd.OFF)
        for t in self.pdlmThreadARR:
            t.stop()
            t.join()
             
    def stop(self):
        self.cleanUp()
        self._stop.set()
        
    def stopped(self):
        return self._stop.isSet()
    
    def getDisplayString(self, uppertext, lowertext):
        return uppertext + "\n" + lowertext
    
    def updateDisplay(self, elems, selected):
        
        upperText = DOUBLEDASH
        lowerText = DOUBLEDASH
        
        # last element
        if selected == (len(elems) -1 ) or len(elems) == 1 :
            upperText = elems[selected].Text
            #lowerText = ""
        else :
            upperText = elems[selected].Text
            lowerText = elems[selected + 1 ].Text

        upperText = upperText.replace(upperText[0:], '*' + upperText[1:])
        print "updateDisplay: childind  {0} : {1}".format(selected, selected + 1)        
        
        
        self.lcd.clear()    
        displayString = self.getDisplayString(upperText, lowerText)
        self.lcd.message(displayString)
        
        self.lastMenuDisplayString = displayString
    
    
    def setDisplayText(self, upperText, lowerText):   
         
         upperText = upperText.center(WIDTH)
         lowerText = lowerText.center(WIDTH)
         
         self.lcd.clear()    
         displayString = self.getDisplayString(upperText, lowerText)
         self.lcd.message(displayString)
         
    
    def setLastDisplayString(self):
        
        self.lcd.clear()
        print "setting last display string"
        print self.lastMenuDisplayString
        self.lcd.message(self.lastMenuDisplayString)
    
    def manageThreads(self, element):
         
         print "lcd managethreads: element tag {}".format(element.tag)
         if element is self.menuobj.tuning :
            self.displayTuning()
         
         elif element is self.menuobj.l2r:
            self.displayAnimation(Animations.LINEAR_L2R)
         
         elif element is self.menuobj.r2l:
            self.displayAnimation(Animations.LINEAR_R2L)
            
         elif element is self.menuobj.toMiddle:
            self.displayAnimation(Animations.MIDDLE_ALL_TO_MIDDLE)
        
         elif element is self.menuobj.fromMiddle:
            self.displayAnimation(Animations.MIDDLE_ALL_FROM_MIDDLE)
            
         elif element is self.menuobj.fieldsFromMiddle:
            self.displayAnimation(Animations.FIELDS_FROM_MIDDLE)
         
         elif element is self.menuobj.fieldsToMiddle:
            self.displayAnimation(Animations.FIELDS_TO_MIDDLE)
            
         elif element is self.menuobj.fieldsl2r:
            self.displayAnimation(Animations.FIELDS_L2R)
         
         elif element is self.menuobj.fieldsr2l:
            self.displayAnimation(Animations.FIELDS_R2L)
            
         elif element is self.menuobj.constantLight:
             self.displayFillAll()
             
         elif element is self.menuobj.metroStart:
             self.displayMetronome()
         
         elif element is self.menuobj.metroTS :
             self.setMetronomeTimeSignature()        
             
         elif element is self.menuobj.singleColor :
             self.chooseColors(FieldColoringTypes.SINGLE)
         
         elif element is self.menuobj.twoColors :
             self.chooseColors(FieldColoringTypes.TWO)
         
         elif element is self.menuobj.multiColor :
             self.chooseColors(FieldColoringTypes.MULTI)
         
         elif element is self.menuobj.spectral : 
             self.displaySpectralAnalysis()
        
         elif element is self.menuobj.updateInverval :
             self.chooseUpdateInterval()
             
         elif element is self.menuobj.maxBrightness : 
             self.setBrightness()     
             
         elif element is self.menuobj.shutdown : 
             self.shutdown()    
             
         else :
            print "war nuescht"   
    
    def displayFillAll(self):
        
        fillThread = pdlmThreads.pdlmFillAll(self.pdlmsettings)
        fillThread.start()
        self.pdlmThreadARR.append(fillThread)
        fillThread.colorFieldDict.printColors()
      
        upperText = "some Color"
        lowerText = "oOooOooOoo"
      
        
        self.setDisplayText(upperText, lowerText)
        
        while not fillThread.isInitialized() :
             sleep(0.1)
             print "not initialized yet"
        
        
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():           
            
             sleep(0.1)
          
        print "displayFillAll: fillAll stopping"
         
        self.pdlmThreadARR.remove(fillThread)
        print "tryin to stop fillThread"
        fillThread.stop()
        fillThread.join()
        
        print "last display string: {}".format(self.lastMenuDisplayString)
        self.setLastDisplayString()
    
    def chooseUpdateInterval(self):
        
        upperText = "set interval"
        interval = self.pdlmsettings.updateInterval
        lowerText = str(interval)
        
        self.setDisplayText(upperText, lowerText)
        print "set color"
        
        sleep(0.2)
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
           
            if self.lcd.buttonPressed(self.lcd.DOWN):
                
                interval = interval - 0.01
                nothingChanged = False
                
            elif self.lcd.buttonPressed(self.lcd.UP):

                interval = interval + 0.01
                nothingChanged = False
            
            elif self.lcd.buttonPressed(self.lcd.LEFT):

                interval = interval - 0.001
                nothingChanged = False
                    
            elif self.lcd.buttonPressed(self.lcd.RIGHT):

                interval = interval + 0.001
                nothingChanged = False
                   
            
            sleep(0.2)
            if not nothingChanged :
                
                if interval < 0.001 :
                    interval = 0.001
                
                lowerText = str("%.4f" % interval)
                print lowerText
                self.setDisplayText(upperText, lowerText)
        
        print "chooseUpdateInverval ending"         
        

        self.pdlmsettings.setUpdateInterval(interval)
        print "setting updateInverval to {}".format(interval)
            
        self.setLastDisplayString()
    
    def setBrightness(self) :
    
        step = 0.1
        upperText = "max Brightness"
        brightness = self.pdlmsettings.maxValue
        lowerText = str(brightness)
        
        self.setDisplayText(upperText, lowerText)
        print "set color"
        
        sleep(0.2)
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
           
            if self.lcd.buttonPressed(self.lcd.DOWN):
                
                brightness = brightness - step
                nothingChanged = False
                
            elif self.lcd.buttonPressed(self.lcd.UP):

                brightness = brightness + step
                nothingChanged = False
            
         
            
            sleep(0.2)
            if not nothingChanged :
                
                if brightness < 0.01 :
                    brightness = 0.1
                elif brightness > 1.0 :
                    brightness = 1.0
                    
                lowerText = str("%.2f" % brightness)
                print lowerText
                self.setDisplayText(upperText, lowerText)
        
        print "setBrightness ending"         
        

        self.pdlmsettings.setMaxBrightness(brightness)
        print "setting max brightness to {}".format(brightness)
            
        self.setLastDisplayString()
    
    def setTonalRange(self):
         
        upperText = "set tonal range"  
        tonalDict = self.pdlmsettings.tonalRangeDict
        keys = tonalDict.viewkeys()
        keyList = list(keys)
        
        i = 0

        lowerText = keyList[i]
        self.setDisplayText(upperText, lowerText)
        print "set color"
        
        sleep(0.2)
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
           
            if self.lcd.buttonPressed(self.lcd.DOWN):
                
                if i < len(keyList) - 1 :
                    i = i + 1
                    lowerText = keyList[i]
                    nothingChanged = False
                
                
            elif self.lcd.buttonPressed(self.lcd.UP):
                if i > 0 :
                    i = i - 1
                    lowerText = keyList[i]
                    nothingChanged = False
                
            
            sleep(0.2)
            print "set Range running"
            if not nothingChanged :
                
                self.setDisplayText(upperText, lowerText)
        
        print "chooseColors ending"         
        

        self.pdlmsettings.setTonalRange(tonalDict[keyList[i]])
        print "setting colors to {}".format(keyList[i])
            
        self.setLastDisplayString()
        
    def chooseColors(self, fieldColoringType):
        
        colDict = dict()
        upperText = "set color"
        
        if fieldColoringType == FieldColoringTypes.SINGLE :
            print "single color"
            colDict = self.pdlmsettings.singleColorDict
        
        elif fieldColoringType == FieldColoringTypes.TWO :
            print "two colors"
            colDict = self.pdlmsettings.twoColorDict
            upperText = upperText + "s"
            
        else :
            print "multi colors"
            colDict = self.pdlmsettings.multiColorDict
            upperText = upperText + "s"
            
        # write keys into a list, so you can access the values with indices
        # and go up and down 
        
        keys = colDict.viewkeys()
        keyList = list(keys)
            
        i = 0

        lowerText = keyList[i]
        self.setDisplayText(upperText, lowerText)
        print "set color"
        
        sleep(0.2)
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
           
            if self.lcd.buttonPressed(self.lcd.DOWN):
                
                if i < len(keyList) - 1 :
                    i = i + 1
                    lowerText = keyList[i]
                    nothingChanged = False
                
                
            elif self.lcd.buttonPressed(self.lcd.UP):
                if i > 0 :
                    i = i - 1
                    lowerText = keyList[i]
                    nothingChanged = False
                
            
            sleep(0.2)
            print "set Color(s) running"
            if not nothingChanged :
                
                self.setDisplayText(upperText, lowerText)
        
        print "chooseColors ending"         
        

        self.pdlmsettings.setFieldColors(colDict[keyList[i]])
        print "setting colors to {}".format(keyList[i])
            
        self.setLastDisplayString()

    
    def displayMetronome(self):
        metronomeThread = pdlmThreads.pdlmMetronome(self.pdlmsettings)
        metronomeThread.start()
        self.pdlmThreadARR.append(metronomeThread)
        
        
        
        while not metronomeThread.isInitialized() :
             sleep(0.1)
             print "not initialized yet"
        
        bpm = metronomeThread.bpm 
        upperText = "BPM"
        lowerText = str(bpm)
        
        self.setDisplayText(upperText, lowerText)
                 
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
            
            if(self.lcd.buttonPressed(self.lcd.LEFT)) : 
                
                bpm = bpm - 1   
                nothingChanged = False
                
            elif self.lcd.buttonPressed(self.lcd.RIGHT):   
                
                bpm = bpm + 1
                nothingChanged = False
            
            elif self.lcd.buttonPressed(self.lcd.UP):
                
                bpm = bpm + 10
                nothingChanged = False
                
                
            elif self.lcd.buttonPressed(self.lcd.DOWN):
                bpm = bpm - 10
                nothingChanged = False
                
            
            sleep(0.2)
            
            if not nothingChanged :
                metronomeThread.setBPM(bpm)
                lowerText = str(bpm)
                self.setDisplayText(upperText, lowerText)
                    
                
            
            print("metronome running")
            
        print "metronome loop stopping"
        
        self.pdlmThreadARR.remove(metronomeThread)
        metronomeThread.stop()
        metronomeThread.join()
        
        self.setLastDisplayString()
        
    def setMetronomeTimeSignature(self):
        
        i = 0
        upperText = "set time sig"
        lowerText = getTSString(TimeSignatures(i))
        self.setDisplayText(upperText, lowerText)
        print "setMetronomeTimeSignature"
        
        sleep(0.2)
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            
            nothingChanged = True
           
            if self.lcd.buttonPressed(self.lcd.DOWN):
                
                if i < len(TIMESIGNATURES) - 1 :
                    i = i + 1
                    lowerText = getTSString(TimeSignatures(i))
                    nothingChanged = False
                
                
            elif self.lcd.buttonPressed(self.lcd.UP):
                if i > 0 :
                    i = i - 1
                    lowerText = getTSString(TimeSignatures(i))
                    nothingChanged = False
                
            
            sleep(0.1)
            print "setMetro TS running"
            if not nothingChanged :
                
                self.setDisplayText(upperText, lowerText)
        
        print "metronomeTimeSignature ending"          
        self.pdlmsettings.timeSignature = TimeSignatures(i) 
        self.setLastDisplayString()
        
    
    def displayAnimation(self, animation):
        
        print "are we here, displayAnimation?"
        self.pdlmsettings.animationType  = animation 
        animThread = pdlmThreads.pdlmAnimation(self.pdlmsettings)
        animThread.start()
        self.pdlmThreadARR.append(animThread)
        
        
        
        while not animThread.isInitialized() :
             sleep(0.1)
             print "not initialized yet"
         
        upperText = "animating".center(WIDTH)
        lowerText = getAnimationName(animation)
        
        self.setDisplayText(upperText, lowerText)       
        while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
            sleep(0.1)
            print("animthread running")
            
        print "displayAnimation: animation Loop stopping"
        
        self.pdlmThreadARR.remove(animThread)
        animThread.stop()
        animThread.join()
        
        print "last display string: {}".format(self.lastMenuDisplayString)
        self.setLastDisplayString()

    def displayTuning(self): #, element):

             
         tunerThread = pdlmThreads.pdlmTuner(self.pdlmsettings)
         tunerThread.start()
         self.pdlmThreadARR.append(tunerThread)
         
         while not tunerThread.isInitialized() :
             sleep(0.1)
             print "not initialized yet"
         
         upperText = "tuning".center(WIDTH)
         while not self.lcd.buttonPressed(self.lcd.SELECT) and not self._stop.isSet():
             #display note on LCD
            
             lowerText = tunerThread.curMidinote.center(WIDTH)
             self.setDisplayText(upperText, lowerText)
             sleep(0.3)
    
         print "displayTuning: tuner loop stopping"

         self.setLastDisplayString()
         
         
         self.pdlmThreadARR.remove(tunerThread)
         print "tryin to stop tunerthread"
         tunerThread.stop()
         tunerThread.join()
    
    def displaySpectralAnalysis(self):
         spectralThread = pdlmThreads.pdlmSpectrumAnalyzer(self.pdlmsettings)
         spectralThread.start()
         self.pdlmThreadARR.append(spectralThread)
         
         while not spectralThread.isInitialized() :
             sleep(0.2)
             print "not initialized yet"
         
         upperText = "analyzing"
         lowerText = "-_-_-"        

         self.setDisplayText(upperText, lowerText)
         
         while (not self.lcd.buttonPressed(self.lcd.SELECT)) and (not spectralThread._stop.isSet()):
            
             sleep(0.2)
         
         print "displaySpectralAnalysis: spectrum loop stopping"
         

         self.setLastDisplayString()
         
         
         self.pdlmThreadARR.remove(spectralThread)
         print "tryin to stop spectralThread"
         spectralThread.stop()
         spectralThread.join()
    
    
    def initializePdlmSettings(self):
        
        #TODO read from textfile
        
        pdlmsettings = pdlmSettings(
                             ledsAndGaps = LEDSANDGAPS, 
                             numLEDs = NUMLEDS, 
                             startIndex = STARTINDEX,
                             endIndex = ENDINDEX,
                             minMidiNote = MINMIDINOTE,
                             maxMidiNote = MAXMIDINOTE,
                          #   minColorH = MINCOLORH,                           
                          #   maxColorH = MAXCOLORH,
                             minSaturationEnergy = MINSATURATIONENERGY, 
                             maxSaturationEnergy = MAXSATURATIONENERGY,
                             minSaturation = MINSATURATION,
                             maxSaturation = MAXSATURATION,
                             minValueEnergy = MINVALUEENERGY,
                             maxValueEnergy = MAXVALUEENERGY,
                             minValue = MINVALUE,
                             maxValue = MAXVALUE,
                             updateInterval = UPDATEINTERVAL,
                             tunerUpdateInterval = TUNERUPDATEINTERVAL,
                             bpm = BPM, 
                             fieldColors = FIELDCOLORS, 
                             reverseLEDorder = REVERSELEDORDER,
                             fullScale = FULLSCALE, 
                             fullNotes = FULLNOTES, 
                             minFreqIntensity = MINFREQINTENSITY,
                             midFreqIntensity = MIDFREQINTENSITY,
                             maxFreqIntensity = MAXFREQINTENSITY,
                             orderFieldLEDsOutIn = ORDERFIELDLEDSOUTIN ,
                             timeSignature = TIMESIGNATURE,
                             correctTuning = CORRECTTUNING)                
                    
        return pdlmsettings
    
     


    
    def shutdown(self):
        
        
        upperText = "yes: sel + ->"
        lowerText = "no: <- "        

         
        self.setDisplayText(upperText, lowerText)
        
        while not self.lcd.buttonPressed(self.lcd.LEFT) and not self._stop.isSet():
             #display note on LCD
            
            if self.lcd.buttonPressed(self.lcd.RIGHT) and self.lcd.buttonPressed(self.lcd.SELECT) :
            
                command = "/usr/bin/sudo /sbin/shutdown -h 0"
                import subprocess
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]
                print output
            sleep(0.2)
            
        self.setLastDisplayString()
