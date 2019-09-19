# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:05:33 2019

@author: johnstonlab

Class of Sequence Acquisition
"""
#Packages import
from PyQt5.QtCore import QThread, pyqtSignal
from time import time, sleep
from multiprocessing.pool import ThreadPool

#Function import
from Labjack import greenOn, greenOff, redOn, redOff, blueOn, blueOff, waitForSignal
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
        ledTimeOn = []
        while(imageCount<(self.nbFrames) and self.acqRunning):
            #Will return only if ARM output signal from the camera raise
            if waitForSignal(self.labjack, "TTL", "AIN", 0): #WaitForSignal return TRUE when AIN0 input is HIGH (>3V)
                #Lighting good LED for next acquisition
                #trigImage(self.labjack) # Trigger the image --> future improvements, use a basic OR gate to get all the LED signal
                if self.ledList[imageCount] == 'r':
                    redOn(self.labjack)
                    start = time()
                    sleep(ledOnDuration)
                    end = time()
                    redOff(self.labjack)
                    ledTimeOn.append(end-start)
                elif self.ledList[imageCount] == 'g':
                    greenOn(self.labjack)
                    start = time()
                    sleep(ledOnDuration)
                    end = time()
                    greenOff(self.labjack)
                    ledTimeOn.append(end-start)
                else:
                    blueOn(self.labjack)
                    start = time()
                    sleep(ledOnDuration)
                    end = time()
                    blueOff(self.labjack)
                    ledTimeOn.append(end-start)
                    
                ##read input from labjack
                saveMetadata(self.textFile, str(time()),self.ledList[(imageCount)], str(imageCount))
                imageCount+=1
        ledFaultCounter = 0
        ledFaultPosition =[]
        for idx, deltaTime in enumerate(ledTimeOn):
            if deltaTime > (ledOnDuration+0.0005) or deltaTime <(ledOnDuration-0.0005):
                ledFaultCounter +=1
                ledFaultPosition.append(idx)
        print 'There are ', ledFaultCounter, ' with non correct illumination time. It concern the following frames :'
        print ledFaultPosition
        
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
        self.imageCount = self._sequenceAcqu()
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