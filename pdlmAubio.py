import pyaudio, struct
from aubio.task import *
from array import *
import threading
import midiNoteMap
import time
from struct import unpack
from pprint import pprint
import numpy as np
from time import sleep
from pdlmSettings import pdlmSettings

class aubioThread(threading.Thread): 
   
   
    def __init__(self,
                 pdlmsettings,
                 CHANNELS=1,
                 PITCHOUT=aubio_pitchm_midi,
                 flagENERGY=False,
                 flagPITCH=True,
                 flagANIM=False):
        
        threading.Thread.__init__(self)
                                  
        self.CHANNELS = pdlmsettings.channels  # number of audio channels
        self.INFORMAT = pdlmsettings.aubioinformat # pyaudio.paInt16
        self.RATE =     pdlmsettings.rate  # sampleRate 16000
        self.FRAMESIZE =pdlmsettings.framesize # size of the chunks
        self.PITCHALG = pdlmsettings.aubiopitchalg # aubio_pitch_yinfft seems to be the fastest
        self.PITCHOUT = PITCHOUT  # type of values you get for pitch detection: aubio_pitchm_freq aubio_pitchm_midi
        self.flagENERGY = flagENERGY  # flag to determine if energy should be calculated
        self.flagPITCH = flagPITCH  # flag to determine if pitch should be calculated
        self.flagANIM = flagANIM
        
        self.curMIDIFLOAT = 0.0  # current value of the midi note as float
        self.curMIDINOTE = ""  # current value of the Midinote as string in the format: "C#-4", used for tuner mode
        self.curOFFSET = 0.0  # the pitch difference from the curMIDINOTE, value between -0.5 and +0.5
        self.curENERGY = 0.0  # current Value of energy
        self.thread_started = False
        
        
        self.daemon = True
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
        
    def stopped(self):
        return self._stop.isSet()
    
    # def runPitching(self):
    def run(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.INFORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.FRAMESIZE)
         
        # set up pitch detect
        if self.flagPITCH or self.flagANIM:
            detect = new_aubio_pitchdetection(self.FRAMESIZE, self.FRAMESIZE / 2, self.CHANNELS,
                                          self.RATE, self.PITCHALG, self.PITCHOUT)
        buf = new_fvec(self.FRAMESIZE, self.CHANNELS)
         
        self.thread_started = True
        # main loop
        runflag = 1
        elapsed = 0.0
       # while runflag:
        while not self._stop.isSet():  # and elapsed < 60 : 
         
             try:
                  start = time.time()
                  # read data from audio input
                  data = stream.read(self.FRAMESIZE)
                 
                  # convert to an array of Integers
                  ints = array('i', data)
                  
                  # copy floats into structure
                  for i in range(len(ints)):
                    fvec_write_sample(buf, ints[i], 0, i)
                    # fvec_write_sample(buf, floats[i], 0, i)
                 
          
                  self.curMIDIFLOAT = aubio_pitchdetection(detect, buf)  # detect,buf)
                  print("AubioMidiFloat: {}".format( self.curMIDIFLOAT))
                      
                  if self.flagPITCH :
                      # separate integer from fractional part 
                      self.curMIDINOTE, self.curOFFSET = midiNoteMap.getTunerValues(self.curMIDIFLOAT) 
               #       print(self.curMIDINOTE)
                     
                      
                  # find energy of audio frame
                  if self.flagENERGY : 
                      try: 
                          self.curENERGY = vec_local_energy(buf)
                          print(self.curENERGY)
                      except: 
                          print("Energy is the problem")
                  
                  elapsed =  (time.time() - start)
               #   print "elapsedTime aubioThred = {}".format(elapsed)
    
               
             except Exception:
                     print "Aubio: better luck next round"
                    
        stream.stop_stream()
        stream.close()
        p.terminate()
        print "Aubio stopped"

# Spectrum Analyzer
class specThread(threading.Thread):
    
    def __init__(self,
                 pdlmsettings,
                 CHANNELS=1,
                # INFORMAT = pyaudio.paInt16,
                # INFORMAT=pyaudio.paFloat32,
              #   RATE=16000,
           #      FRAMESIZE=4096
             ):
        
        threading.Thread.__init__(self)
                                  
        self.CHANNELS = pdlmsettings.channels # CHANNELS  # number of audio channels
        self.INFORMAT = pdlmsettings.specinformat  #INFORMAT  # pyaudio.paInt16
        self.RATE =     pdlmsettings.rate # sampleRate 16000
        self.FRAMESIZE =pdlmsettings.framesize # FRAMESIZE  # size of the chunks
        self.curOFFSET = 0.0  # the pitch difference from the curMIDINOTE, value between -0.5 and +0.5
        self.curENERGY = 0.0  # current Value of energy
        self.thread_started = False
    
        self.matrix = []
        self.matrix.extend(0 for x in range(pdlmsettings.numFields))
       
        pprint("len matrix: {0}, matrix {1}".format(len(self.matrix), self.matrix))
        self.power = []
        # as a rule of thumb as the frequency doubles, the power halves
        
        #self.weighting = [2 ** x for x in range(pdlmsettings.numFields)]  # Change these according to taste
        self.weighting = [4.0, 8.0, 8.0, 10.0, 9.0]  # Change these according to taste
        pprint("len weighting: {0}, weighting {1}".format(len(self.weighting), self.weighting))
               
        self.daemon = True
        self._stop = threading.Event()
    

        self.numFields = pdlmsettings.numFields
          
        #self.updateInterval = pdlmsettings.updateInterval 
        
        
        print"EQ initalized"
    
    def stop(self):
        self._stop.set()
        
    def stopped(self):
        return self._stop.isSet()
    
    def run(self):
        
        print"trying to run Spectrum Analyzer"
        
        print"self.FRAMESIZE {}".format(self.FRAMESIZE)
        print"self.INFORMAT {}".format(self.INFORMAT)
        print"self.RATE {}".format(self.RATE)
        
        p = pyaudio.PyAudio()
        stream = p.open(format=self.INFORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.FRAMESIZE)
         


        buf = new_fvec(self.FRAMESIZE, self.CHANNELS)
         
        self.thread_started = True
        # main loop
        runflag = 1
        elapsed = 0.0
        while not self._stop.isSet():  # and elapsed < 60 : 
         
            try:
                  print("***** start loop ***** ")
                  start = time.time()
                  # read data from audio input
                  data = stream.read(self.FRAMESIZE)
                 # print("len(data) = {}".format(len(data)))
                 
                  self.calculate_levels(data)
                 
       #           for i in range(0, len(self.matrix)):
        #              print("matrix[i] = {0}, i = {1}".format(self.matrix[i], i))
                  
                  elapsed = time.time() - start
                  
                 # print("time elapsed: {}".format(elapsed))
    
                #  sleep(self.updateInterval)
            except Exception as e:
                    print "EQ Aubio: better luck next round, \n {}".format(e.message)
                    
        stream.stop_stream()
        stream.close()
        p.terminate()
        print "specThread stopped"
        
    def calculate_levels(self, data):
           
        try: 
               print("-_-_-_-_-_-_-_-_-_-_-_Calculate Levels-_-_-_-_-_-_-_-_-_-_-_")
                   # Convert raw data to numpy array
               data = unpack("%dh" % (len(data) / 2), data)
    #           print("len(data) = {}".format(len(data)))
               
               # Apply FFT - real data
               fourier = np.fft.rfft(data)
               # Remove last element in array to make it the same size as chunk
               fourier = np.delete(fourier, len(fourier) - 1)
               # Find average 'amplitude' for specific frequency ranges in Hz
               power = np.abs(fourier)   
      #         pprint(power)
               # sorry for hardcoding the values and the frequency bands ;)
               self.matrix[0] = int(np.mean(power[self.piff(0)    :self.piff(400):1]))
               self.matrix[1] = int(np.mean(power[self.piff(400)  :self.piff(750):1]))
               self.matrix[2] = int(np.mean(power[self.piff(750)  :self.piff(1500):1]))
               self.matrix[3] = int(np.mean(power[self.piff(1500) :self.piff(3000):1]))
               self.matrix[4] = int(np.mean(power[self.piff(3000) :self.piff(10000):1]))
           
               # Tidy up column values for the LED matrix
               self.matrix = np.divide(np.multiply(self.matrix, self.weighting), 1000000)

        except Exception as e:
                    print "calculate_levels: \n {}".format(e.message)

    def piff(self, val):
           return int(2 * self.FRAMESIZE * val / self.RATE)
    
   
