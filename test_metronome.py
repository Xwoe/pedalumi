#import aubioOperations
#! /usr/bin/python

import threading
import signal
import sys
# import pdlmThreads
from pdlmThreads import pdlmMetronome 
import pdlmLCD
from time import sleep
from pdlmEnums import Animations, TimeSignatures
from pprint import pprint
from pdlmSettings import pdlmSettings


#     LINEAR_L2R                  = 1
#     LINEAR_R2L                  = 2
#     MIDDLE_ALL_FROM_MIDDLE      = 3
#     MIDDLE_ALL_TO_MIDDLE        = 4
#     FIELDS_FROM_MIDDLE          = 5
#     FIELDS_TO_MIDDLE            = 6
#     FIELDS_L2R                  = 7
#     FIELDS_R2L                  = 8

NUMLEDS = 44
ANIM = Animations.MIDDLE_ALL_TO_MIDDLE
REVERSELEDORDER = True
UPDATEINTERVAL = 0.01

MINMIDINOTE = 40
MAXMIDINOTE = 86

MINCOLOR = 0.0
MAXCOLOR = 360.0


LEDSANDGAPS = (10,2,8,2,8,2,8,2,10)

THREADARR = []

BPM = 90
TIMESIGNATURE = TimeSignatures._5_4


# this gets executed when Ctrl-C is pressed

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    
    for t in THREADARR:
        t.stop()
        t.join()

    sys.exit(0)
    
    
signal.signal(signal.SIGINT, signal_handler)



    

        
def main():   
    

#     print(ANIM)
#     print(MINMIDINOTE)
#     print(MAXMIDINOTE)
#     print(MINCOLOR)
#     print(MAXCOLOR)
#     print(UPDATEINTERVAL)
#     print(REVERSELEDORDER)
#     pprint(LEDSANDGAPS)
     
    settings = pdlmSettings(LEDSANDGAPS,
                        ANIM, 
                        minMidiNote = MINMIDINOTE,
                        maxMidiNote = MAXMIDINOTE,
                        minColor = MINCOLOR,
                        maxColor = MAXCOLOR,
                        updateInterval = UPDATEINTERVAL, 
                        reverseLEDorder = True,
                        fullScale = True,
                        fullNotes = True,
                        bpm = BPM,
                        timeSignature = TIMESIGNATURE) 
    pdlmThread = pdlmMetronome(settings)  
    pdlmThread.setDaemon(True)
    pdlmThread.start()   
     
    THREADARR.append(pdlmThread)

    
    runflag = 1
    while runflag: 
    
         print 'still running'
    
         sleep(1)
     
    

if  __name__ =='__main__':main()
