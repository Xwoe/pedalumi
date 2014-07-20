#! /usr/bin/python

import threading
import signal
import sys
import pdlmLCD
from time import sleep


THREADARR = []


# this gets executed when Ctrl-C is pressed

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    
    for t in THREADARR:
        t.stop()
        t.join()

    sys.exit(0)
    
    
signal.signal(signal.SIGINT, signal_handler)

      
def main():   


        lcdthread = pdlmLCD.pdlmLCDthread()
        lcdthread.start()
        THREADARR.append(lcdthread)
    
        runflag = 1
        while runflag: 
        
             print 'still running'
        
             sleep(1)
         
    

if  __name__ =='__main__':main()
 