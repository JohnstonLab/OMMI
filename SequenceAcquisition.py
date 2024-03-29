# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:05:33 2019

@author: Johnstonlab

Class of Sequence Acquisition
"""
#Packages import
from PyQt5.QtCore import QThread, pyqtSignal
from time import time, sleep
from multiprocessing.pool import ThreadPool


#Class Import
from ArduinoTeensy import Arduino
from SignalInterrupt import SignalInterrupt

#Function import
import ArduinoTeensy
from Labjack import greenOn, greenOff, redOn, redOff, blueOn, blueOff, waitForSignal, readSignal, readOdourValve, trigImage, risingEdge
from saveFcts import filesInit, emptyTiffDel, tiffWritersClose, saveFrame, saveMetadata, cfgFileSaving
import saveFcts



class SequenceAcquisition(QThread):
    """
    Class for sequence acquisition object.
    Source for QThread management (inspiration) :  https://nikolak.com/pyqt-threading-tutorial/
                            https://medium.com/@webmamoffice/getting-started-gui-s-with-python-pyqt-qthread-class-1b796203c18c
                                --> https://gist.github.com/WEBMAMOFFICE/fea8e52c8105453628c0c2c648fe618f (source code)
    """
    nbFramesSig = pyqtSignal(int)
    progressSig = pyqtSignal(int)
    isFinished = pyqtSignal()
    isStarted = pyqtSignal()
    arduinoSyncStarted = pyqtSignal()
    arduinoSyncFinished = pyqtSignal()

    #Color mode in R-B acquisition
    rbColorModes = ['Red and Blue', 'Red only', 'Blue only']

    def __init__(self, mmc, labjack, parent=None):
        QThread.__init__(self,parent)

        #Add the camera and the labjack
        self.mmc = mmc
        self.labjack = labjack

        self.acqRunning = True

        #Initialize with information from the GUI
        self.experimentName = None
        self.duration = None
        self.cycleTime = None
        self.rgbLedRatio = None
        self.greenFrameInterval = None
        self.maxFrames = None
        self.expRatio = None
        self.colorMode = None
        self.folderPath = None

        #Initialized in other method of this class
        self.nbFrames = None
        self.ledList = None     #Initialized in _sequenceInit method
        self.tiffWriterList = None  #Initialized in filesInit method from SaveFcts.py
        self.textFile = None        #Initialized in filesInit method from SaveFcts.py
        self.acquMode = None
        self.seqMode = None

        self.startAcquisitionTime = None
        self.stimName = None
        self.loopRunning = True #by default we need to have this value set to True for the frameSaving thread


    def __del__(self):
        self.wait()

    def _rgbSequenceInit(self):
        """
        Set the LEDs sequence list in function of the time of the experiment.
        This function will take 3 LED ratio and make a list
        with each of these ratios on the pattern [xR,yG,zB]
        """
        ## send all of this to sequence acq
        if not self.nbFrames:
            self.nbFrames = int(self.duration/self.cycleTime)+1  ## Determine number of frames. (+1) because int round at the lower int
        self.ledSeq = [0]*self.rgbLedRatio[0]+[1]*self.rgbLedRatio[1]+[2]*self.rgbLedRatio[2] #Sequence of LED lighting in function of the ratio
                                                                                #RED = 0
                                                                                #GREEN = 1
                                                                                #BLUE = 2
        print('LED sequence : ', self.ledSeq)
        self.ledList = self.ledSeq*(int(self.nbFrames/(len(self.ledSeq)))+1) ## schedule LED lighting
        #NB : no return needed because each ledList and nbFrames are instance attribute

    def _rbSequenceInit(self):
        """
        Set the LEDs sequence list in function of the time of the experiment.
        This function generate list with an alternance of red (0) and blue (2)
        frames with some green (1) frame at precise interval
        """

        ## send all of this to sequence acq
        if not self.nbFrames:
            self.nbFrames = int(self.duration/self.cycleTime)+1 ## Determine number of frames. (+1) because int round at the lower int
        #nbGreenFrames = self.rbGreenRatio[0] #nb of green frames in each green sequence #NOT YET USED
        nbGreenSequence = float(self.nbFrames)/self.greenFrameInterval #Dividing nbFrames by the green frame interval with a float to have float division
        print('Nb of green frames : ', nbGreenSequence)
        nbGreenSequence = int(round(nbGreenSequence))
        print('Nb of green frames : ', nbGreenSequence)
        #if self.colorMode == SequenceAcquisition.rbColorModes[0]:
        colorSeq=[0,2] #R & B alternation by default
        if self.colorMode == SequenceAcquisition.rbColorModes[1]:
            colorSeq = [0] #Red only mode
        elif self.colorMode == SequenceAcquisition.rbColorModes[2]:
            colorSeq = [2] #Blue only mode

        self.ledList = colorSeq*int(round(float(self.nbFrames-nbGreenSequence)/len(colorSeq))) #Initiate a whole list of R-B alternance
        #list.insert(index, elem) -- inserts the element at the given index, shifting elements to the right
        greenSeqIdx = 0
        while greenSeqIdx <= self.nbFrames :
            self.ledList.insert(greenSeqIdx,1)
            greenSeqIdx+= self.greenFrameInterval
        #NB : no return needed because each ledList and nbFrames are instance attribute


    def _ledSwitching(self, ledOnDuration):
        """
        In charge of switching LED and saving metadata in a .txt file
        """
        imageCount=0
        print('Transmitted ledOnDuration value : ',ledOnDuration)

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
        print('end of the ledSwitchingThread')
        return imageCount

    def _frameSaving(self):
        """
        In charge of saving frames
        """
        self.mmc.clearCircularBuffer()
        imageCount=0
        self.mmc.startContinuousSequenceAcquisition(1)
        while(imageCount<(self.nbFrames) and self.acqRunning and self.loopRunning):
            if self.mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished #Enter this loop BETWEEN acquisition
                #trigImage(labjack) #Generate a pulse, which allows to flag the entry in this code statement with the oscilloscope
                img = self.mmc.popNextImage() #Gets and removes the next image from the circular buffer
                saveFrame(img, self.tiffWriterList, (imageCount), self.maxFrames) # saving frame of previous acquisition
                imageCount +=1
                self.progressSig.emit(imageCount)



        #Stop camera acquisition #Ensure that no more frames are taken
        self.mmc.stopSequenceAcquisition()

        #### IF ABORTED acquisition #####
        self._circularBufferCleaning(imageCount)

        #Close tiff file open
        tiffWritersClose(self.tiffWriterList)
        print('end of the _frameSavingThread')
        return imageCount

    def _circularBufferCleaning(self, imageCount):
        """
        Get the last images in the circular buffer if the acquisition was aborted.
        This step ensure that there is the same amount of metadata than frames saved.
        """
        if (not self.acqRunning) or (not self.loopRunning): #Check if sequence acquisition was aborted or loop was paused.
            print(('cycleTime :',self.cycleTime))
            sleep(self.cycleTime)
            print(('remaining images in the circular buffer :',self.mmc.getRemainingImageCount()))
            while(self.mmc.getRemainingImageCount() > 0):
                print('getting last image, num : ', imageCount)
                img = self.mmc.popNextImage() #Gets and removes the next image from the circular buffer
                saveFrame(img, self.tiffWriterList, (imageCount), self.maxFrames) # saving frame of previous acquisition
                imageCount +=1
                sleep(self.cycleTime)
            #Close tiff file open
            tiffWritersClose(self.tiffWriterList)
            if ((self.nbFrames/self.maxFrames)>=1): #check that multiples .tif were initialized
                # --> CHECK WICH .tif are empty and suppress it
                if self.stimName:
                    emptyTiffDel(self.stimName,
                                  self.savePath,
                                  imageCount,
                                  self.maxFrames,
                                  self.tiffWriterList)
                else:
                    emptyTiffDel(self.experimentName,
                                  self.savePath,
                                  imageCount,
                                  self.maxFrames,
                                  self.tiffWriterList)

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
        print('New-Seq_acq')
        exp = (self.mmc.getExposure())*0.001 #converted in s
        ledOnDuration = exp*self.expRatio[0]
        print('time LED ON (s) : ', ledOnDuration)

        print("Nb of frames : ", self.nbFrames)
        imageCount = 0

        pool = ThreadPool(processes=2)
        print('Pool initialized')

        frameSavingThread = pool.apply_async(self._frameSaving,())
        sleep(0.005) ## WAIT FOR INITIALIZATION AND WAITFORSIGNAL FCT
        ledSwitchingThread = pool.apply_async(self._ledSwitching,(ledOnDuration,))
        imageCount = ledSwitchingThread.get()
        print('Saving process counter : ', frameSavingThread.get())
        print('LED process counter : ', imageCount)
        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
        print('sequ acq done')
        return imageCount

    def _metadataSaving(self):
        """
        Listening to the FIRE signal and save each metadat when a rising edge
        is detected.
        """
        imageCount=0

        #Timestamp to flag the beginning of acquisition
        if not self.startAcquisitionTime:
            self.startAcquisitionTime = time()
        print('timestamp got')
        while(imageCount<(self.nbFrames) and self.acqRunning and self.loopRunning):
            if risingEdge(self.labjack, 3): #Labjack, channel, timeout(s)
                startTime = time()
                frameTime = startTime - self.startAcquisitionTime #Taking the off time to be synchronized with metadata
                odourValveSig = readOdourValve(self.labjack, 2)
                respirationSig = readSignal(self.labjack, 0)
                saveMetadata(	self.textFile,
								str(frameTime),
								str(self.ledList[imageCount]),
								str(imageCount),
								str(odourValveSig),
								str(respirationSig),
								str(0)) #Maybe not the best practice
                imageCount+=1

        #close the metadata .txt file
        self.textFile.close()
        print('end of the ledSwitchingThread')
        return imageCount


    def _seqAcqCyclops(self):
        """
        Prepare and start the sequence acquisition. Write frame in an tiff file
        during acquisition.
        This function use the onboard arduino of the led driver to alternate the
        LEDs.
        Sequence acquisition is triggered internally using the command from MMC API.
        --> Inputs and outputs :
            - USB connection to each LED driver (arduino Teensy port)
            - INPUT SELECT from each LED driver on DAC
            - Camera.FIRE > Labjack.AIN3
            - Camera.ARM > Labjack.AIN0
        """
        print('Cyclops running')

        pool = ThreadPool(processes=2)
        print('Pool initialized')

        ledSwitchingThread = pool.apply_async(self._metadataSaving,())
        sleep(0.001) ## WAIT FOR INITIALIZATION AND WAITFORSIGNAL FCT
        frameSavingThread = pool.apply_async(self._frameSaving,())
        imageCount = ledSwitchingThread.get()
        print('Saving process counter : ', frameSavingThread.get())
        print('LED process counter : ', imageCount)
        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
        print('sequ acq done')
        return imageCount



    def arduinoSync(self):
        """
        Send informations about the coming sequence acquisition to the arduino
        inside each LED drivers
        """
        self.arduinoSyncStarted.emit()
        #Calculation of the time LED must be on
        exp = (self.mmc.getExposure()) # in ms
        #list containing each illumTime for each LED
        illumTime=[round(exp*self.expRatio[0],3),
                   round(exp*self.expRatio[1],3),
                   round(exp*self.expRatio[2],3)]

        if self.seqMode == "rgbMode":
            ledDriverNb=[0,1,2] #[Red, Green, Blue]
            for driverNb in ledDriverNb:
                driver = Arduino(driverNb)
                driver.synchronization(illumTime,
                                       rgbLedRatio = self.rgbLedRatio)
        elif self.seqMode == 'rbMode':
            ledDriverNb=[0,1,2] #[Red, Green, Blue]
            for driverNb in ledDriverNb:
                driver = Arduino(driverNb)
                driver.synchronization(illumTime,
                                       greenFrameInterval = self.greenFrameInterval,
                                       colorMode = self.colorMode)

        self.arduinoSyncFinished.emit()

    def sequencePreparation(self):
        """
        Prepare a sequence acquisition setting up all the parameters.
        """
        #Calculation of the number of frames in function of the duration + LED list for the acquisition
        if self.seqMode == "rgbMode":
            self._rgbSequenceInit()
        elif self.seqMode == 'rbMode':
            self._rbSequenceInit()
        else:
            print('Please select a valid mode of led sequence initialization')
        #Sending nb of frames to initialize the progress bar
        if type(self.nbFrames) == int:
            self.nbFramesSig.emit(self.nbFrames)

        print('acquisition Side : ', self.expRatio)
        #Saving the configuration of the experiment file (.json)
        self.savePath = cfgFileSaving(self.experimentName,
                                      self.nbFrames,
                                      self.duration,
                                      self.expRatio,
                                      self.acquMode,
                                      self.seqMode,
                                      self.rgbLedRatio,
                                      self.greenFrameInterval,
                                      round(1/self.cycleTime,2), #framerate
                                      self.folderPath,
                                      self.colorMode,
                                      self.mmc,
                                      'Zyla') #WARNING > modulabilty (there is a way to get device label but it's not so easy)

        #initialization of the acquisition saving files : .tif (frames) and .txt (metadata)
        (self.tiffWriterList, self.textFile) = filesInit(   self.savePath,
                                                            self.experimentName,
                                                            self.nbFrames,
                                                            self.maxFrames)
        #send all informations to each LED driver
        self.arduinoSync()

    def loopFolderPreparation(self):
        """
        Create a config
        """
        #Calculation of the number of frames in function of the duration + LED list for the acquisition
        # THIS IS USEFUL FOR THE LABJACK MODE ONLY
#        if self.seqMode == "rgbMode":
#            self._rgbSequenceInit()
#        elif self.seqMode == 'rbMode':
#            self._rbSequenceInit()
#        else:
#            print('Please select a valid mode of led sequence initialization')
        #Sending nb of frames to initialize the progress bar

        #Saving the configuration of the experiment file (.json)
        self.savePath = cfgFileSaving(self.experimentName,
                                      self.nbFrames,
                                      self.duration,
                                      self.expRatio,
                                      self.acquMode,
                                      self.seqMode,
                                      self.rgbLedRatio,
                                      self.greenFrameInterval,
                                      round(1/self.cycleTime,2), #framerate approx
                                      self.folderPath,
                                      self.colorMode,
                                      self.mmc,
                                      'Zyla') #WARNING > modulabilty (there is a way to get device label but it's not so easy)



    def _loopPreparation(self, stimNumber):
        """
        Init files for a loop acquisition
        """
        self.nbFrames=10000 #TO DO --> better place for this line of code

        self.stimName= self.experimentName+'_S%(number)03d' % {"number": stimNumber} #%02d return a 2 char string : 1-->01
        (self.tiffWriterList, self.textFile) = filesInit(   self.savePath,
                                                            self.stimName,
                                                            self.nbFrames,
                                                            self.maxFrames)
        if self.seqMode == "rgbMode":
            self._rgbSequenceInit()
        elif self.seqMode == 'rbMode':
            self._rbSequenceInit()
        self.arduinoSync()

    def run(self):
        self.isStarted.emit()
        #Launching the frame acquisition
#        if self.acquMode == "Labjack":
#            print'sequ acq about to start'
#            self.imageCount = self._sequenceAcqu()
#            print'run fct done'
        if self.acquMode == "Run":
            #self.arduinoSync()
            self.imageCount = self._seqAcqCyclops()
        elif self.acquMode == "Loop":

            interruptAIN = 1
            stopSignalState = False
            waitToCheckSignal = 0.5
            #Instanciate a SignalInterrupt object to listen to the labjack and the moment when SYNC signal goes low
            self.stopInterrupt = SignalInterrupt(self.labjack, interruptAIN, waitToCheckSignal, stopSignalState)
            self.stopInterrupt.stateReachedInterrupt.connect(self.pauseLoop)
            self.stopInterrupt.start()

            stimNumber = 1
            self.startAcquisitionTime = time()
            print('start acquisition time :', self.startAcquisitionTime)
            while(self.acqRunning):
                print('Stimulation nb ', stimNumber)
                self._loopPreparation(stimNumber)
                #Wait for the raise of the SYNC signal
                #if waitForSignal(self.labjack, channel=1): #waitForSignal(device, signalType="TTL", channelType="AIN", channel=1)
                while(not risingEdge(self.labjack, interruptAIN)) and self.acqRunning:
                    continue
                if self.acqRunning:
                    self.loopRunning = True
                    self.imageCount = self._seqAcqCyclops()
                    print(self.imageCount)
                    stimNumber += 1
                else:
                    #Close tiff file open
                    tiffWritersClose(self.tiffWriterList)
                    #close the metadata .txt file
                    self.textFile.close()
                    saveFcts.acqFilesDel(self.stimName,self.savePath)
                    print('abort loop')
            self.stopInterrupt.abort() #Stop the listenning action of the Interrupt


        else:
            print('Please select a valid mode of triggering the LED')

        print('end of the thread')
        self.isFinished.emit()

    def pauseLoop(self):
        """
        Pause the acquisition in the loop mode. Action triggered by the end of a stim sync signal
        """
        print('SYNC stim detected LOW')
        self.loopRunning = False

    def abort(self):
        """
        Interrupt the threads running for LED switching and frame saving.
        """
        try:
            self.acqRunning = False
        except:
            print('Cannot abort properly')
