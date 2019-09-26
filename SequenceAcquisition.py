# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:05:33 2019

@author: johnstonlab

Class of Sequence Acquisition
"""
#Packages import
from PyQt5.QtCore import QThread, pyqtSignal
from time import time, sleep, clock
from multiprocessing.pool import ThreadPool

#Function import
from Labjack import greenOn, greenOff, redOn, redOff, blueOn, blueOff, waitForSignal, readSignal, readOdourValve
from saveFcts import filesInit, tiffWriterDel, tiffWritersClose, saveFrame, saveMetadata, cfgFileSaving


class SequenceAcquisition(QThread):
    """
    Class for sequence acquisition object.
    Source for QThread management (inspiration) :  https://nikolak.com/pyqt-threading-tutorial/
                            https://medium.com/@webmamoffice/getting-started-gui-s-with-python-pyqt-qthread-class-1b796203c18c
                                --> https://gist.github.com/WEBMAMOFFICE/fea8e52c8105453628c0c2c648fe618f (source code)
    """
    nbFramesSig = pyqtSignal(int)
    progressSig = pyqtSignal(int)
    

    
    def __init__(self, experimentName, duration, cycleTime, rgbLedRatio, rbGreenRatio, maxFrames, expRatio, mmc, labjack, parent=None):
        QThread.__init__(self,parent)
        
        #Set instance attributes
        self.experimentName = experimentName
        self.duration = duration
        self.cycleTime = cycleTime
        self.rgbLedRatio = rgbLedRatio
        self.rbGreenRatio = rbGreenRatio
        self.maxFrames = maxFrames
        self.expRatio = expRatio
        self.mmc = mmc
        self.labjack = labjack
        self.acqRunning = True
        self.nbFrames = None    #Initialized in _sequenceInit method
        self.ledList = None     #Initialized in _sequenceInit method
        self.tiffWriterList = None  #Initialized in filesInit method from SaveFcts.py
        self.textFile = None        #Initialized in filesInit method from SaveFcts.py
        self.savePath = None        #Initialized in filesInit method from SaveFcts.py
        self.acquMode = None
        self.seqMode = None
        

    def __del__(self):
        self.wait()
            
    def _rgbSequenceInit(self):
        """
        Set the LEDs sequence list in function of the time of the experiment. 
        This function will take 3 LED ratio and make a list 
        with each of these ratios on the pattern [xR,yG,zB]
        """
        ## send all of this to sequence acq
        self.nbFrames = int(self.duration/self.cycleTime)+1  ## Determine number of frames. (+1) because int round at the lower int
        ledSeq = [0]*self.rgbLedRatio[0]+[1]*self.rgbLedRatio[1]+[2]*self.rgbLedRatio[2] #Sequence of LED lighting in function of the ratio
                                                                                #RED = 0
                                                                                #GREEN = 1
                                                                                #BLUE = 2
        print 'LED sequence : ', ledSeq
        self.ledList = ledSeq*(int(self.nbFrames/(len(ledSeq)))+1) ## schedule LED lighting
        #NB : no return needed because each ledList and nbFrames are instance attribute
        
    def _rbSequenceInit(self):
        """
        Set the LEDs sequence list in function of the time of the experiment.
        This function generate list with an alternance of red (0) and blue (2)
        frames with some green (1) frame at precise interval
        """
        
        ## send all of this to sequence acq
        self.nbFrames = int(self.duration/self.cycleTime)+1 ## Determine number of frames. (+1) because int round at the lower int
        #nbGreenFrames = self.rbGreenRatio[0] #nb of green frames in each green sequence #NOT YET USED
        greenFrameInterval = self.rbGreenRatio[1] #Interval between each green sequence (nb of frames)
        nbGreenSequence = float(self.nbFrames)/greenFrameInterval #Dividing nbFrames by the green frame interval with a float to have float division
        print 'Nb of green frames : ', nbGreenSequence
        nbGreenSequence = int(round(nbGreenSequence))
        print 'Nb of green frames : ', nbGreenSequence
        self.ledList = [0,2]*int(round(float(self.nbFrames-nbGreenSequence)/2)) #Initiate a whole list of R-B alternance
        #list.insert(index, elem) -- inserts the element at the given index, shifting elements to the right
        greenSeqIdx = 0
        while greenSeqIdx <= self.nbFrames :
            self.ledList.insert(greenSeqIdx,1)
            greenSeqIdx+= greenFrameInterval
        #NB : no return needed because each ledList and nbFrames are instance attribute


    def _ledSwitching(self, ledOnDuration):
        "In charge of switching LED and saving metadata in a .txt file"
        imageCount=0
        print 'Transmitted ledOnDuration value : ',ledOnDuration
        
        #Timestamp to flag the beginning of acquisition 
        startAcquisitionTime = time()
        while(imageCount<(self.nbFrames) and self.acqRunning):
            #Will return only if ARM output signal from the camera raise
            #to check if the camera is ready to receive trigger signal
            if waitForSignal(self.labjack, "TTL", "AIN", 0): 	#WaitForSignal return TRUE when AIN0 input is HIGH (>3V),
                
                onTime = time()		#flag the begining of a LED illumination
                if self.ledList[imageCount] == 0: 	#RED
                    redOn(self.labjack)
                    sleep(ledOnDuration)
                    redOff(self.labjack)
                elif self.ledList[imageCount] == 1:	#GREEN
                    greenOn(self.labjack)
                    sleep(ledOnDuration)
                    greenOff(self.labjack)
                else:								#BLUE
                    blueOn(self.labjack)
                    sleep(ledOnDuration)
                    blueOff(self.labjack)
                offTime = time()	#flag the end of a LED illumination
                
                effectiveLedOnDuration = offTime-onTime
                frameTime = offTime - startAcquisitionTime #Taking the off time to be synchronized with metadata
                odourValveSig = readOdourValve(self.labjack, 2)
                respirationSig = readSignal(self.labjack, 3)
                saveMetadata(	self.textFile, 
								str(frameTime),
								str(self.ledList[imageCount]), 
								str(imageCount), 
								str(odourValveSig), 
								str(respirationSig), 
								str(effectiveLedOnDuration))
                imageCount+=1
        
        
        #close the metadata .txt file
        self.textFile.close()
        print 'end of the ledSwitchingThread'
        return imageCount
        
    def _frameSaving(self):
        "In charge of saving frames and actualize the GUI"
        self.mmc.clearCircularBuffer() 
        imageCount=0
        self.mmc.startContinuousSequenceAcquisition(1)
        while(imageCount<(self.nbFrames) and self.acqRunning):
            if self.mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished #Enter this loop BETWEEN acquisition
                #trigImage(labjack) #Generate a pulse, which allows to flag the entry in this code statement with the oscilloscope
                img = self.mmc.popNextImage() #Gets and removes the next image from the circular buffer
                ##read input from labjack
                saveFrame(img, self.tiffWriterList, (imageCount), self.maxFrames) # saving frame of previous acquisition
                imageCount +=1
                self.progressSig.emit(imageCount)
        
        #Close tiff file open
        tiffWritersClose(self.tiffWriterList)
        
        #### IF ABORTED acquisition --> CHECK WICH .tif are empty and suppress it #####
        print(self.acqRunning)
        print(self.nbFrames/self.maxFrames)
        if (not self.acqRunning) and ((self.nbFrames/self.maxFrames)>=1): #check if abort fct was called and that multiples .tif were initialized
            tiffWriterDel(self.experimentName, self.savePath, imageCount, self.maxFrames, self.tiffWriterList)
        
        #Stop camera acquisition
        self.mmc.stopSequenceAcquisition()
        print 'end of the _frameSavingThread'
        return imageCount
    
    
    def _sequenceAcqu(self):
        """
        Prepare and start the sequence acquisition. Write frame in an tiff file during acquisition. 
        This function use the labjack to detect a camera trigger.
        --> Inputs and outputs :
            - Camera.ARM > Labjack.AIN0
            - Camera.TRIGGER > Labjack.FIO7
            - Labjack.FIO4 > blue
            - Labjack.FIO5 > red
            - Labjack.FIO6 > green
    
        Source for multithreading : https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
        Doc for multithreading : https://docs.python.org/2/library/multiprocessing.html
        """
        print 'New-Seq_acq'
        exp = (self.mmc.getExposure())*0.001 #converted in ms
        ledOnDuration = exp*self.expRatio
        print 'time LED ON (s) : ', ledOnDuration
        
        print "Nb of frames : ", self.nbFrames
        imageCount = 0
        
        pool = ThreadPool(processes=2)
        print 'Pool initialized'
        
        frameSavingThread = pool.apply_async(self._frameSaving,())
        sleep(0.005) ## WAIT FOR INITIALIZATION AND WAITFORSIGNAL FCT
        ledSwitchingThread = pool.apply_async(self._ledSwitching,(ledOnDuration,))
        #guiUpdatingThread = pool.apply_async(guiUpdating,(duration, app, exit,))
        print 'Saving process counter : ', frameSavingThread.get()
        imageCount = ledSwitchingThread.get()
        print 'LED process counter : ', imageCount
        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
        
        return imageCount

    def _seqAcqCyclops(self):
        print 'Cyclops running'
        print "Nb of frames : ", self.nbFrames
        imageCount = 0
        
        self.mmc.startContinuousSequenceAcquisition(1)

        while(imageCount<(self.nbFrames) and self.acqRunning): #Loop stops if we have the number of frames wanted OR if abort button is press (see abortFunc)
            
            #Saving frame coming in the circular buffer
            if self.mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished #Enter this loop BETWEEN acquisition
                #trigImage(self.labjack) #Generate a pulse, which allows to flag the entry in this code statement with the oscilloscope
                #Lighting good LED for next acquisition
#                if self.ledList[imageCount] == 'r':
#                    #print "Blue off"
#                    greenOff(self.labjack)
#                    redOn(labjack)
#                elif ledList[imageCount] == 'g':
#                    redOff(labjack)
#                    greenOn(labjack)
#                else:
#                    redOff(labjack)
#                    greenOff(labjack)
                #sleep(0.005) #Wait 5ms to ensure LEDS are on
                t = clock()
                img = self.mmc.popNextImage() #Gets and removes the next image from the circular buffer
                ##read input from labjack
                valveValue = readOdourValve(self.labjack, 2)
                saveMetadata(self.textFile, str(t),self.ledList[imageCount], str(imageCount), str(valveValue()))
                saveFrame(img, self.tiffWriterList, imageCount, self.maxFrames) # saving frame of previous acquisition
                imageCount +=1
        
        #Close tiff file open
        tiffWritersClose(self.tiffWriterList)
        
        
        #Stop camera acquisition
        self.mmc.stopSequenceAcquisition()
        self.mmc.clearCircularBuffer() 
        return imageCount
        
    
    def run(self):
        print 'run fct'
        
        #Calculation of the number of frames in function of the duration + LED list for the acquisition
        if self.seqMode == "rgbMode":
            self._rgbSequenceInit()
        elif self.seqMode == 'rbMode':
            self._rbSequenceInit()
        else:
            print('Please select a valid mode of led sequence initialization')
        #Sending nb of frames to initialize the progress bar
        self.nbFramesSig.emit(self.nbFrames)
        
        #Saving the configuration of the experiment file (.json)
        self.savePath = cfgFileSaving(self.experimentName, 
                                      self.nbFrames, 
                                      self.duration,
                                      self.expRatio,
                                      self.acquMode,
                                      self.seqMode,
                                      self.rgbLedRatio,
                                      self.rbGreenRatio,
                                      round(1/self.cycleTime,2), #framerate
                                      self.mmc, 
                                      'Zyla') #WARNING > modulabilty
        
        #initialization of the acquisition saving files : .tif (frames) and .txt (metadata)
        (self.tiffWriterList, self.textFile) = filesInit(   self.savePath,
                                                            self.experimentName,
                                                            self.nbFrames, 
                                                            self.maxFrames)
        #Launching the frame acquisition
        if self.acquMode == "Labjack":
            print'sequ acq about to start'
            self.imageCount = self._sequenceAcqu()
            print'sequ acq done'
        elif self.acquMode == "Cyclops":
            self.imageCount = self._seqAcqCyclops()
        else:
            print 'Please select a valid mode of triggering the LED'
        
        print 'end of the thread'
            
    def abort(self):
        
        try:
            #Closing all files opened
            self.textFile.close()
            tiffWritersClose(self.tiffWriterList)
        except:
            print 'Cannot close files'
            
        try:
            self.acqRunning = False
        except:
            print 'Cannot abort properly'
