# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 10:51:18 2019

@author: Louis Vande Perre

Main file of ISOI software.
v2 - using thread to launch an acquisition.

"""

#Packages import
import sys
import MMCorePy
import cv2
from PyQt5 import QtWidgets, uic
#from time import sleep, time

#Class import
from SequenceAcquisition import SequenceAcquisition
from LiveHistogram import LiveHistogram

#Function import
from histogram import histoInit, histoCalc
from crop import crop_w_mouse
from continousAcq import grayLive, sequenceAcqSoftTrig, sequenceAcqCamTrig, sequenceInit , sequenceAcqLabjackTrig, sequenceAcqLabjackTrig2, guiUpdating
from camInit import camInit
from saveFcts import filesInit, fileSizeCalculation, tiffWriterDel, tiffWritersClose, saveFrame, saveMetadata
from Labjack import labjackInit, greenOn, greenOff, redOn, redOff, blueOn, blueOff, risingEdge, waitForSignal, trigImage
from ArduinoComm import connect, sendExposure, sendLedList, close

########## GLOBAL VAR - needed for displays information ######

#Allows to abort an acquisition
#global exit
#exit = Event()



class isoiWindow(QtWidgets.QMainWindow):
    ### Class attributes - needed for displays information ###
    
    #trackbar
    div=100
    step=1/float(div)
    
    #Exposure (just here to keep it as global var)
    #expMin=0.0277
    expMin=5.0
    expMax=99.0
    
    #LEDs Ratio
    ledFrameNbMax=10
    ledFrameNbMin=0
    
    #File Size params
    fileSizeMax =4.
    fileSizeMin =0.5
    fileSizeStep =0.5
    fileSizeDefault =1.
    
    #LED lit time (as a ratio of the exposure time) 
    ratioMin = 0.05
    ratioMax = 1.
    ratioDefault = 0.7
    ratioStep = 0.05
    
    #Bit depth (cam properties)
    bit= ['12-bit (high well capacity)','12-bit (low noise)',"16-bit (low noise & high well capacity)"]
    
    #Binning (cam properties)
    binn=['1x1','2x2','4x4','8x8']
    
    def __init__(self, mmc, DEVICE, labjack,parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('isoi_window_V2.ui', self)
        
        ### Instance attributes ##
        self.mmc = mmc
        self.DEVICE = DEVICE
        self.labjack = labjack
        
        # Connect push buttons
        self.cropBtn.clicked.connect(self.crop)
        self.histoBtn.clicked.connect(self.launchHisto)
        self.SaveEBtn.clicked.connect(self.paramCheck)
        self.SaveEBtn.setEnabled(True)
        self.trigBtn.clicked.connect(self.oldHisto)
        self.abortBtn.setEnabled(False)
        self.loadBtn.clicked.connect(self.loadZyla)
        self.unloadBtn.clicked.connect(self.unloadDevices)
        
        ###### ComboBoxes ######
        
        #Binning selection
        self.binBox.addItem(isoiWindow.binn[0])
        self.binBox.addItem(isoiWindow.binn[1])
        self.binBox.addItem(isoiWindow.binn[2])
        self.binBox.addItem(isoiWindow.binn[3])
        self.binBox.currentIndexChanged.connect(self.binChange)
        
        #Bit depth selection
        self.bitBox.addItem(isoiWindow.bit[0])
        self.bitBox.addItem(isoiWindow.bit[1])
        self.bitBox.addItem(isoiWindow.bit[2])
        self.binBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Binning'))
        self.bitBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Sensitivity/DynamicRange'))
        self.bitBox.currentIndexChanged.connect(self.bitChange)
        
        #Shutter mode selection
        self.shutBox.addItem("Rolling")
        self.shutBox.addItem("Global")
        self.shutBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'ElectronicShutteringMode'))
        self.shutBox.currentIndexChanged.connect(self.shutChange)
        
        #Trigger mode selection
        self.triggerBox.addItem('Internal (Recommended for fast acquisitions)')
        self.triggerBox.addItem('Software (Recommended for Live Mode)')
        self.triggerBox.addItem('External Start')
        self.triggerBox.addItem('External Exposure')
        self.triggerBox.addItem('External')
        self.triggerBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'TriggerMode'))
        self.triggerBox.currentIndexChanged.connect(self.triggerChange)
        
        #LEDs trigger mode selection
        self.ledTrigBox.addItem('Camera')
        self.ledTrigBox.addItem('Software')
        self.ledTrigBox.addItem('Labjack - Cyclops mode')
        self.ledTrigBox.addItem('Labjack - Custom mode')
        self.ledTrigBox.setCurrentText('Software')
        
        #Overlap Mode
        self.overLapBox.addItem('On')
        self.overLapBox.addItem('Off')
        self.overLapBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Overlap'))
        self.overLapBox.currentIndexChanged.connect(self.overlapChange)
        
        ####### Slider #####
        self.expSlider.setMinimum(isoiWindow.expMin)
        self.expSlider.setMaximum(isoiWindow.expMax)
        self.expSlider.setValue(self.mmc.getExposure())  
        self.expSlider.valueChanged.connect(self.expFunc)
        self.expSlider.setSingleStep(isoiWindow.step)
        
        #### Spinboxes ###
        
        #EXPOSURE
        self.C_expSb.setMaximum(isoiWindow.expMax)
        self.C_expSb.setMinimum(isoiWindow.expMin)
        self.C_expSb.setValue(self.mmc.getExposure())
        self.C_expSb.valueChanged.connect(self.expFunc)
        self.C_expSb.setSingleStep(isoiWindow.step)
        
        #Experiment duration
        self.dur.setSingleStep(float(isoiWindow.step))
        self.dur.setMaximum(1000)
        
        #LEDs ratios
        self.gRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.rRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.bRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.gRatio.setMaximum(isoiWindow.ledFrameNbMax)
        self.rRatio.setMaximum(isoiWindow.ledFrameNbMax)
        self.bRatio.setMaximum(isoiWindow.ledFrameNbMax)
        
        #File size
        self.fileSize.setValue(isoiWindow.fileSizeDefault)
        self.fileSize.setSingleStep(isoiWindow.fileSizeStep)
        self.fileSize.setMaximum(isoiWindow.fileSizeMax)
        self.fileSize.setMinimum(isoiWindow.fileSizeMin)
        self.fileSize.valueChanged.connect(self.fileSizeSetting)
      
        #Interval Ms
        self.expRatio.setValue(isoiWindow.ratioDefault)
        self.expRatio.setMaximum(isoiWindow.ratioMax)
        self.expRatio.setSingleStep(isoiWindow.ratioStep)
        self.expRatio.setMinimum(isoiWindow.ratioMin)
        
        #####
        
        #Name text area
        self.name.insert("DefaultName")
        
        #Initialize frames per files text label
        self.framesPerFileLabel.setText('1146') #nb frames per file (1GB) for uncropped frame with 16 bits per pixels
        
        #Initialize exposure label
        self.realExp.setText(str(self.mmc.getExposure()))
        
        #ProgressBar
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        
        #LEDs toggle buttons
        self.Green.stateChanged.connect(self.green)
        self.Red.stateChanged.connect(self.red)
        self.Blue.stateChanged.connect(self.blue)
        
    
    def liveFunc(self): #Not connected
        grayLive(self.mmc)
        
    def crop(self):
        self.mmc.clearROI()
        self.mmc.snapImage()
        img = self.mmc.getImage()
        (x,y,w,h) = crop_w_mouse(img, self.mmc.getROI())
        self.mmc.setROI(x,y,w,h)
        print "image width: "+str(self.mmc.getImageWidth())
        print "image height: "+str(self.mmc.getImageHeight())
        cv2.destroyAllWindows()
    
    def expFunc(self, expVal):
        #exp=expVal/float(div)
        self.C_expSb.setValue(expVal) #update spinbox value
        self.expSlider.setValue(expVal) #update slider value
        print 'exposure wanted : ', expVal
        try:
            self.mmc.setExposure(DEVICE[0], expVal)
            self.realExp.setText(str(self.mmc.getExposure()))
        except:
            print "CMM err, no possibility to set exposure"
            
    def binChange(self):
        binn = self.binBox.currentText()
        self.mmc.setProperty(self.DEVICE[0], 'Binning', str(binn))
        print "Binning set at", self.mmc.getProperty(self.DEVICE[0],'Binning') 

    def bitChange(self):
        bit = self.bitBox.currentText()
        self.mmc.setProperty(self.DEVICE[0], 'Sensitivity/DynamicRange', str(bit))
        print "Bit depth set at", self.mmc.getProperty(self.DEVICE[0],'Sensitivity/DynamicRange')
        
    def shutChange(self):
        shut = self.shutBox.currentText()
        self.mmc.setProperty(self.DEVICE[0],'ElectronicShutteringMode',str(shut))
        print 'Shutter mode set at ', self.mmc.getProperty(self.DEVICE[0], 'ElectronicShutteringMode')

    def triggerChange(self):
        trig = self.triggerBox.currentText()
        self.mmc.setProperty(self.DEVICE[0],'TriggerMode',str(trig))
        print 'Trigger mode set at ', self.mmc.getProperty(self.DEVICE[0], 'TriggerMode')

    def overlapChange(self):
        overlap = self.overLapBox.currentText()
        try:
            self.mmc.setProperty(self.DEVICE[0],'Overlap', str(overlap))
            print 'Overlap set at ', self.mmc.getProperty(self.DEVICE[0], 'Overlap')
        except:
            print "CMM err, no possibility to set Overlap mode"
    def green(self,toggle_g):
        if toggle_g:
            greenOn(self.labjack)
        else :
            greenOff(self.labjack)
          
    def red(self,toggle_r):
        if toggle_r:
            redOn(self.labjack)
        else :
            redOff(self.labjack)    
            
    def blue(self,toggle_b):
        if toggle_b:
            blueOn(self.labjack)
        else :
            blueOff(self.labjack)
    
    
    def fileSizeSetting(self):
        sizeMax = self.fileSize.value()
        ROI = self.mmc.getROI()
        bitDepth = self.bitBox.currentText()
        if bitDepth == isoiWindow.bit[2]:
            bitPPix = 16 #Nb of bits per pixel
        else:
            bitPPix = 12
        
        framesMax = fileSizeCalculation(sizeMax, ROI, bitPPix)
        self.framesPerFileLabel.setText(str(framesMax))
    
    def unloadDevices(self):
        self.mmc.unloadAllDevices()
        print 'all devices UNLOADED'
        return True
    
    def closeEvent(self, event):
        # Close all before closing the main window
        if self.unloadDevices(): # UNLOAD DEVICES befor closing the program
            event.accept() # let the window close
        else:
            event.ignore()
        
    def loadZyla(self):
        self.DEVICE = camInit(self.mmc)
        print 'Device ',self.DEVICE[0],' loaded'
    
    def paramCheck(self):
        """ Check that the user is well informed about certains acquisition settings before launching the acquisition"""
        run = True
        
        #Shutter mode check
        if mmc.getProperty(DEVICE[0], 'ElectronicShutteringMode')== 'Rolling':
            choice = QtWidgets.QMessageBox.question(self, 'Shutter Mode',
                                                "Running acquisition in Rolling mode ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                print("Running in Rolling mode")
                run = True
            else:
                print('Change mode in the other panel')
                run = False
                
        #Arduino synchronization check        
        if (self.ledTrigBox.currentText() == 'Camera' and run):
            choice = QtWidgets.QMessageBox.question(self, 'Cyclops driver initialisation',
                                                "Are the cyclops Arduino synchronized ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.No:
                print("sending exposur to arduino")
                run = self.arduinoSync()
            else:
                print('are you sure you have update it ???')
                run = True
                
        if run:
            self.saveImageSeq()
            
    def saveImageSeq(self):
        #Get experiment/acquisition settings from the GUI
        name = self.name.text() #str
        duration = self.dur.value()*1000 # int (+conversion in ms)
        ledRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] #list of int
        maxFrames =  int(self.framesPerFileLabel.text()) #int
        expRatio = self.expRatio.value()
        
         
        #Creation of a SequenceAcquisition class instance
        self.sequencAcq = SequenceAcquisition(name, 
                                         duration, 
                                         ledRatio,
                                         maxFrames,
                                         expRatio,
                                         self.mmc,
                                         self.labjack)
        print 'object initialized'
        self.sequencAcq.finished.connect(self.acquisitionDone)
        self.sequencAcq.nbFramesSig.connect(self.initProgressBar)
        self.sequencAcq.progressSig.connect(self.updateProgressBar)
        # We have all the events we need connected we can start the thread
        #print 'object connected'
        self.sequencAcq.start()
        print 'object started'
        # At this point we want to allow user to stop/terminate the thread
        # so we enable that button
        self.abortBtn.setEnabled(True)
        # And we connect the click of that button to the built in
        # terminate method that all QThread instances have
        self.abortBtn.clicked.connect(self.sequencAcq.abort)
        # We don't want to enable user to start another thread while this one is
        # running so we disable the start button.
        self.SaveEBtn.setEnabled(False)
    
    ##### Methods in charge of communication with SequenceAcquisition class instance ####
    def initProgressBar(self,nbFrames):
        #Initialize progressBar
        self.progressBar.setMaximum(nbFrames)
        
    def updateProgressBar(self,imageCount):
        self.progressBar.setValue(imageCount+1)
    
    def acquisitionDone(self):
        print 'acquisition done'
        #reset progressBar
        self.progressBar.reset()
        #Change button state
        self.abortBtn.setEnabled(False)
        self.SaveEBtn.setEnabled(True)
        
        
    ##### HISTOGRAM FCT ####
    def launchHisto(self):
        try:
            self.liveHistogram = LiveHistogram(self.mmc, self.labjack)
            # Connections between LED settings button and histogram
            self.liveHistogram.modeChoice.connect(self.askHistoMode)
            self.liveHistogram.finished.connect(self.histoDone)
            
            self.liveHistogram.start()  
        except:
            print 'cannot instanciate the LiveHistogram class'
            
    def oldHisto(self):
        (mask, h_h, h_w, pixMaxVal, bin_width, nbins) = histoInit(mmc)
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        self.mmc.snapImage()
        g = self.mmc.getImage() #Initialize g
        self.mmc.startContinuousSequenceAcquisition(1)
        while True:
                if self.mmc.getRemainingImageCount() > 0:
                    g = self.mmc.getLastImage()
                    rgb2 = cv2.cvtColor(g.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[g>(pixMaxVal-2)]=mask[g>(pixMaxVal-2)]*256 #It cannot be compared to pixMaxVal because it will never reach this value
                    cv2.imshow('Video', rgb2)
                        
                else:
                    print('No frame')
                    
                h = histoCalc(nbins, pixMaxVal, bin_width, h_h, h_w, g)
                cv2.imshow('Histogram',h)
                
                if cv2.waitKey(33) == 27:
                    break
                if cv2.getWindowProperty('Video', 1) == -1: #Condition verified when 'X' (close) button is pressed
                    break
                elif cv2.getWindowProperty('Histogram', 1) == -1: #Condition verified when 'X' (close) button is pressed
                    break

        cv2.destroyAllWindows()
        self.mmc.stopSequenceAcquisition()
            
    ### Methods in charge of communication with LiveHisto class instance
    def askHistoMode(self):
        print 'popup window to ask mode'
        
        #Selection between blinking or continous mode histogram
        
        #Change in toggle boxes connection
        self.reconnect(self.Green.stateChanged, self.launchBlinkingMode) #Disconnect green led from green function
        self.reconnect(self.Red.stateChanged, self.launchBlinkingMode) #Disconnect green led from green function
        self.reconnect(self.Blue.stateChanged, self.launchBlinkingMode) #Disconnect green led from green function
    
    def launchBlinkingMode(self):
        print 'LaunchBlinking mode'
        if self.Green.isChecked() and not self.Red.isChecked() and not self.Blue.isChecked():
            self.liveHistogram.led = 'g'
            self.liveHistogram.blinkingLedMode()
            print 'green LED blinking mode'
        elif self.Red.isChecked() and not self.Blue.isChecked() and not self.Green.isChecked():
            print 'red LED blinking mode'
        elif self.Blue.isChecked() and not self.Red.isChecked() and not self.Green.isChecked():
            print 'blue LED blinking mode'
        elif not self.Blue.isChecked() and not self.Red.isChecked() and not self.Green.isChecked():
            print 'black histogram'
        else:
            print 'Turn on only one LED before lauching histogram'
        #self.liveHistogram.blinkingLedMode()
        
    def histoDone(self):
        print 'Histo done'
        #Change in toggle boxes connection
        self.reconnect(self.Green.stateChanged, self.green) #Disconnect green led from green function
        self.reconnect(self.Red.stateChanged, self.red) #Disconnect green led from green function
        self.reconnect(self.Blue.stateChanged, self.blue) #Disconnect green led from green function
        
        
    def reconnect(self, signal, newhandler=None, oldhandler=None):
        """
        Source : https://stackoverflow.com/questions/21586643/pyqt-widget-connect-and-disconnect
        """
        while True:
            try:
                if oldhandler is not None:
                    signal.disconnect(oldhandler)
                else:
                    signal.disconnect()
                print 'disconnection OK'
            except TypeError:
                break
        if newhandler is not None:
            signal.connect(newhandler)
            print 'new connection ok'


##Launching everything
if __name__ == '__main__':
    
    """MicroManager Init"""
    mmc = MMCorePy.CMMCore()
    
    """Camera Init"""
    DEVICE = camInit(mmc) # TO FIX, give DEVICE at some function only
    
    """Labjack init"""
    labjack = labjackInit()
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = isoiWindow(mmc, DEVICE, labjack)
    window.show()
    sys.exit(app.exec_())