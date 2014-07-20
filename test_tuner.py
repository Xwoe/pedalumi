#import aubioOperations
#! /usr/bin/python

import threading
import signal
import sys
import pdlmThreads
import pdlmLCD
from time import sleep
from pdlmSettings import pdlmSettings
import pyaudio, struct
from aubio.task import *


NUMLEDS = 44
STARTINDEX = 33
ENDINDEX = 10
THREADARR = []
LEDSANDGAPS = (10,2,8,2,8,2,8,2,10)
AUBIORATE = 32000
FRAMESIZE = 4096
AUBIOPITCHALG = aubio_pitch_fcomb
UPDATEINTERVAL = 0.05
REVERSELEDORDER = True
 
# this gets executed when Ctrl-C is pressed

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    
    for t in THREADARR:
        t.stop()
        t.join()

    sys.exit(0)
    
    
signal.signal(signal.SIGINT, signal_handler)


        
def main():   
    
    settings = pdlmSettings(LEDSANDGAPS, 
                            numLEDs = NUMLEDS, 
                            startIndex = STARTINDEX, 
                            endIndex = ENDINDEX, 
                            rate = AUBIORATE, 
                            framesize = FRAMESIZE, 
                            aubiopitchalg = AUBIOPITCHALG,
                            tunerUpdateInterval = UPDATEINTERVAL,
                            reverseLEDorder = REVERSELEDORDER)

    pdlmThread = pdlmThreads.pdlmTuner(settings)
    pdlmThread.start()   
     
    THREADARR.append(pdlmThread)

    
    runflag = 1
    while runflag: 
    
         print 'still running'
    
         sleep(1)
     
    

if  __name__ =='__main__':main()
