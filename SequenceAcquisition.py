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
from saveFcts import filesInit, tiffWriterDel, tiffWritersClose, saveFrame, saveMetadata


class SequenceAcquisition(QThread):
    """
    Class for sequence acquisition object.
    Source for QThread management (inspiration) :  https://nikolak.com/pyqt-threading-tutorial/
                            https://medium.com/@webmamoffice/getting-started-gui-s-with-python-pyqt-qthread-class-1b796203c18c
                                --> https://gist.github.com/WEBMAMOFFICE/fea8e52c8105453628c0c2c648fe618f (source code)
    """
    nbFramesSig = pyqtSignal(int)
    progressSig = pyqtSignal(int)
    

    
    def __init__(self, experimentName, duration, ledRatio, maxFrames, expRatio, mmc, labjack, parent=None):
        QThread.__init__(self,parent)
        
        #Set instance attributes
        self.experimentName = experimentName
        self.duration = duration
        self.ledRatio = ledRatio
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
        

    def __del__(self):
        self.wait()
            
    def _sequenceInit(self):
        """Prepare infos about the sequence acq coming"""
        readOutFrame = 10 #ms ##Minimal time between 2 frames (cf page 45 zyla hardware guide)
        ## send all of this to sequence acq
        self.nbFrames = int((self.duration)/(readOutFrame+self.mmc.getExposure()))+1  ## Determine number of frames. (+1) because int round at the lower int
        ledSeq = ['r']*self.ledRatio[0]+['g']*self.ledRatio[1]+['b']*self.ledRatio[2] #Sequence of LED lighting in function of the ratio
        print 'LED sequence : ', ledSeq
        self.ledList = ledSeq*(int(self.nbFrames/(len(ledSeq)))+1) ## schedule LED lighting
        #NB : no return needed because each ledList and nbFrames are instance attribute


    def _ledSwitching(self, ledOnDuration):
        "In charge of switching LED and saving metadata in a .txt file"
        imageCount=0
        print 'Transmitted ledOnDuration value : ',ledOnDuration
        
        #Timestamp to flag the beginning of acquisition 
        startAcquisitionTime = time()
        while(imageCount<(self.nbFrames) and self.acqRunning):
            #Will return only if ARM output signal from the camera raise
            if waitForSignal(self.labjack, "TTL", "AIN", 0): #WaitForSignal return TRUE when AIN0 input is HIGH (>3V)
                #Lighting good LED for next acquisition
                #trigImage(self.labjack) # Trigger the image --> future improvements, use a basic OR gate to get all the LED signal
                onTime = time()
                if self.ledList[imageCount] == 'r':
                    #onTime = clock()
                    redOn(self.labjack)
                    sleep(ledOnDuration)
                    redOff(self.labjack)
                    #offTime = clock()
                elif self.ledList[imageCount] == 'g':
                    #onTime = clock()
                    greenOn(self.labjack)
                    sleep(ledOnDuration)
                    greenOff(self.labjack)
                    #offTime = clock()
                else:
                    #onTime = clock()
                    blueOn(self.labjack)
                    sleep(ledOnDuration)
                    blueOff(self.labjack)
                    #offTime = clock()
                offTime = time()
                
                effectiveLedOnDuration = offTime-onTime
                frameTime = onTime - startAcquisitionTime
                valveValue = readOdourValve(self.labjack, 2)
                saveMetadata(self.textFile, str(frameTime),self.ledList[(imageCount)], str(imageCount), str(valveValue), str(effectiveLedOnDuration))
                imageCount+=1
#        #Print LED fault counter
#        ledFaultCounter = 0
#        ledFaultPosition =[]
#        for idx, deltaTime in enumerate(ledTimeOn):
#            if deltaTime > (ledOnDuration+0.0001) or deltaTime <(ledOnDuration-0.0001):
#                ledFaultCounter +=1
#                ledFaultPosition.append(idx)
#        print 'There are ', ledFaultCounter, ' frames with non correct illumination time. It concern the following frames :'
#        print ledFaultPosition
#        
#        #Print delay on labjack functions
#        print '\n ON delays \n'
#        for delay in onDelay:
#            print delay
#        print '\n OFF delays \n'
#        for delay in offDelay:
#            print delay
        
        
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
        self._sequenceInit()
        #Sending nb of frames to initialize the progress bar
        self.nbFramesSig.emit(self.nbFrames)
        #initialization of the saving files : .tif (frames) and .txt (metadata)
        (self.tiffWriterList, self.textFile,self.savePath) = filesInit( self.experimentName,
                                                                        self.nbFrames, 
                                                                        self.maxFrames)
        #Launching the frame acquisition
        if self.acquMode == "Labjack":
            self.imageCount = self._sequenceAcqu()
        elif self.acquMode == "Cyclops":
            self.imageCount = self._seqAcqCyclops()
        else:
            print 'Please select a valid mode of triggering the LED'
        print 'Image Count : ', self.imageCount
        
        #Closing all files opened
        self.textFile.close()
        tiffWritersClose(self.tiffWriterList)
        #### IF ABORTED acquisition --> CHECK WICH .tif are empty and suppress it #####  
        if not self.acqRunning and ((self.nbFrames/self.maxFrames)>=1): #check if abort fct was called and that multiples .tif were initialized
            tiffWriterDel(self.experimentName, self.savePath, self.imageCount, self.maxFrames, self.tiffWriterList)
        
        print 'end of the thread'
            
    def abort(self):
        print 'things to do before abort'
        try:
            self.acqRunning = False
        except:
            print 'Cannot abort properly'