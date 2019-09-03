# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 10:46:56 2019

@author: Louis Vande Perre

Main file of ISOI software.
v1 using the demo cam from MM

TASK :
    1. Connect buttons and parameters set up
    2. Run short experiment with different LEDs on
    3. Metadata writing and checking experiment + correct folders names
    4. Saving each 512 frames
    
TO DO :
    - TO fix : minimize global vars number + modulability
"""
#Packages import
import sys
import MMCorePy
import matplotlib.pyplot as plt
import numpy as np
import cv2
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from time import sleep
from threading import Event

#Function import

from crop import crop_w_mouse
from histogram import histoInit, histoCalc
from continousAcq import grayLive, sequenceAcqSoftTrig, sequenceAcqCamTrig, sequenceInit, sequenceAcqTriggered, multipleSnap
from camInit import camInit
from saveFcts import tiffWriterInit, fileSizeCalculation, tiffWriterDel, tiffWriterClose
from Labjack import labjackInit, greenOn, greenOff, redOn, redOff, trigImage, trigExposure
from ArduinoComm import connect, sendExposure, close

########## GLOBAL VAR - needed for displays information ######

#Allows to abort an acquisition
global exit
exit = Event()

#trackbar
div=100
step=1/float(div)

#Exposure (just here to keep it as global var)
#expMin=0.0277
expMin=5.0
expMax=99.0

#LEDs Ratio
ratioMax=10
ratioMin=0

#Bit depth (cam properties)
bit= ['12-bit (high well capacity)','12-bit (low noise)',"16-bit (low noise & high well capacity)"]

#Binning (cam properties)
binn=['1x1','2x2','4x4','8x8']

class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('isoi_window.ui', self)
        
        # Connect buttons 
        self.liveBtn.clicked.connect(self.liveFunc)
        self.cropBtn.clicked.connect(self.crop)
        self.histoBtn.clicked.connect(self.histo)
        self.SaveEBtn.clicked.connect(self.shutterModeCheck)
        self.triggerBtn.clicked.connect(self.triggerExt)
        self.abortBtn.clicked.connect(self.abortFunc)
        self.loadBtn.clicked.connect(self.loadZyla)
        self.unloadBtn.clicked.connect(self.unloadDevices)
        
        ###### ComboBoxes ######
        
        #Binning selection
        self.binBox.addItem(binn[0])
        self.binBox.addItem(binn[1])
        self.binBox.addItem(binn[2])
        self.binBox.addItem(binn[3])
        self.binBox.currentIndexChanged.connect(self.binChange)
        
        #Bit depth selection
        self.bitBox.addItem(bit[0])
        self.bitBox.addItem(bit[1])
        self.bitBox.addItem(bit[2])
        self.binBox.setCurrentText(mmc.getProperty(DEVICE[0], 'Binning'))
        self.bitBox.setCurrentText(mmc.getProperty(DEVICE[0], 'Sensitivity/DynamicRange'))
        self.bitBox.currentIndexChanged.connect(self.bitChange)
        
        #Shutter mode selection
        self.shutBox.addItem("Rolling")
        self.shutBox.addItem("Global")
        self.shutBox.setCurrentText(mmc.getProperty(DEVICE[0], 'ElectronicShutteringMode'))
        self.shutBox.currentIndexChanged.connect(self.shutChange)
        
        #Trigger mode selection
        self.triggerBox.addItem('Internal (Recommended for fast acquisitions)')
        self.triggerBox.addItem('Software (Recommended for Live Mode)')
        self.triggerBox.addItem('External Start')
        self.triggerBox.addItem('External Exposure')
        self.triggerBox.addItem('External')
        self.triggerBox.setCurrentText(mmc.getProperty(DEVICE[0], 'TriggerMode'))
        self.triggerBox.currentIndexChanged.connect(self.triggerChange)
        
        #LEDs trigger mode selection
        self.ledTrigBox.addItem('Camera')
        self.ledTrigBox.addItem('Software')
        self.ledTrigBox.setCurrentText('Software')
        self.ledTrigBox.currentIndexChanged.connect(self.ledTrigChange)
        
        
        ####### Slider #####
        self.expSlider.setMinimum(expMin)
        self.expSlider.setMaximum(expMax)
        self.expSlider.setValue(mmc.getExposure())  
        self.expSlider.valueChanged.connect(self.expFunc)
        self.expSlider.setSingleStep(step)
        
        #### Spinboxes ###
        
        #EXPOSURE
        self.C_expSb.setMaximum(expMax)
        self.C_expSb.setMinimum(expMin)
        self.C_expSb.setValue(mmc.getExposure())
        self.C_expSb.valueChanged.connect(self.expFunc)
        self.C_expSb.setSingleStep(step)
        
        #Experiment duration
        self.dur.setSingleStep(float(step))
        
        #LEDs ratios
        self.gRatio.setMinimum(ratioMin)
        self.rRatio.setMinimum(ratioMin)
        self.bRatio.setMinimum(ratioMin)
        self.gRatio.setMaximum(ratioMax)
        self.rRatio.setMaximum(ratioMax)
        self.bRatio.setMaximum(ratioMax)
        
        #File size
        self.fileSize.setValue(1.)
        self.fileSize.setSingleStep(0.5)
        self.fileSize.setMaximum(4.)
        self.fileSize.setMinimum(0)
        self.fileSize.valueChanged.connect(self.fileSizeSetting)
        
        #Interval Ms
        self.intervalMs.setValue(1.)
        self.intervalMs.setMinimum(1)
        
        #####
        
        #Name text area
        self.name.insert("DefaultName")
        
        #Initialize frames per files text label
        self.framesPerFileLabel.setText('1146') #nb frames per file (1GB) for uncropped frame with 16 bits per pixels
        
        #Initialize exposure label
        self.realExp.setText(str(mmc.getExposure()))
        
        #ProgressBar
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        
        #LEDs toggle buttons
        self.Green.stateChanged.connect(self.green)
        self.Red.stateChanged.connect(self.red)
        #self.BLUE.stateChanged.connect(self.blue)
        
    def liveFunc(self):
        grayLive(mmc)
        
    def crop(self):
        mmc.clearROI()
        mmc.snapImage()
        img = mmc.getImage()
        (x,y,w,h) = crop_w_mouse(img, mmc.getROI())
        mmc.setROI(x,y,w,h)
        print "image width: "+str(mmc.getImageWidth())
        print "image height: "+str(mmc.getImageHeight())
        cv2.destroyAllWindows()
    
    def expFunc(self, expVal):
        #exp=expVal/float(div)
        self.C_expSb.setValue(expVal) #update spinbox value
        self.expSlider.setValue(expVal) #update slider value
        print 'exposure wanted : ', expVal
        try:
            mmc.setExposure(DEVICE[0], expVal)
            self.realExp.setText(str(mmc.getExposure()))
        except:
            print "CMM err, no possibility to set exposure"
            
    def binChange(self):
        binn = self.binBox.currentText()
        mmc.setProperty(DEVICE[0], 'Binning', str(binn))
        print "Binning set at", mmc.getProperty(DEVICE[0],'Binning') 

    def bitChange(self):
        bit = self.bitBox.currentText()
        mmc.setProperty(DEVICE[0], 'Sensitivity/DynamicRange', str(bit))
        print "Bit depth set at", mmc.getProperty(DEVICE[0],'Sensitivity/DynamicRange')
        
    def shutChange(self):
        shut = self.shutBox.currentText()
        mmc.setProperty(DEVICE[0],'ElectronicShutteringMode',str(shut))
        print 'Shutter mode set at ', mmc.getProperty(DEVICE[0], 'ElectronicShutteringMode')
    def triggerChange(self):
        trig = self.triggerBox.currentText()
        mmc.setProperty(DEVICE[0],'TriggerMode',str(trig))
        print 'Trigger mode set at ', mmc.getProperty(DEVICE[0], 'TriggerMode')
    def ledTrigChange(self):
        if (self.ledTrigBox.currentText() == 'Camera'):
            choice = QtWidgets.QMessageBox.question(self, 'Cyclops driver initialisation',
                                                "Do you want to update red LED script ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                print("sending exposur to arduino")
                ser = connect()
                if ser:
                    sendExposure(ser, int(float(mmc.getExposure())))
                    print 'Exposure set at : ',ser.readline()
                    close(ser)
                else:
                    print('Check wire connections')
            else:
                print('are you sure you have update it ???')
    
    def green(self,toggle_g):
        if toggle_g:
            greenOn(labjack)
        else :
            greenOff(labjack)
          
    def red(self,toggle_r):
        if toggle_r:
            redOn(labjack)
        else :
            redOff(labjack)

        
    def fileSizeSetting(self):
        sizeMax = self.fileSize.value()
        ROI = mmc.getROI()
        bitDepth = self.bitBox.currentText()
        if bitDepth == bit[2]:
            bitPPix = 16 #Nb of bits per pixel
        else:
            bitPPix = 12
        
        framesMax = fileSizeCalculation(sizeMax, ROI, bitPPix)
        self.framesPerFileLabel.setText(str(framesMax))
    

    def triggerExt(self):
        duration = self.dur.value()*1000 ## get duration from spinbox and converted it in ms
        ledRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] # [r,g,b]## get LED ratio
        intervalMs = self.intervalMs.value()
        exp = mmc.getExposure(DEVICE[0])
        #Initialise sequence acqu
        #(ledList, nbFrames) = sequenceInit(duration, ledRatio, int(float(mmc.getProperty(DEVICE[0], 'Exposure'))), intervalMs)
        
        #sequenceAcqTriggered(mmc,nbFrames, DEVICE[0], intervalMs, labjack)
        print 'External trigger to snap image'
        #mmc.snapImage()
        mmc.clearCircularBuffer()
        print 'image ready to snap'
        for i in range(0,10):
            sleep(1)
            print(10-i)
        #trigExposure(labjack, exp)
        trigImage(labjack)
        failureCount=0
        while(failureCount<5000):
            if mmc.getRemainingImageCount() > 0:
                print 'Circular buffer is not empty'
                img = mmc.popNextImage()
                plt.imshow(img, cmap='gray')
                plt.show()
            else:
                sleep(0.001)
                failureCount+=1
        print 'Failure count : ', failureCount
#        mmc.clearCircularBuffer()
#        trigImage(labjack)
#        failureCount=0
#        exp = float(mmc.getProperty(DEVICE[0], 'Exposure'))
#        while(failureCount<10):
#            sleep(exp*0.001)
#            if (mmc.getRemainingImageCount() > 0):
#                img = mmc.popNextImage()
#                plt.imshow(img, cmap='gray')
#                plt.show()
#            else:
#                print 'no frame'
#                failureCount+=1
        print 'trig done'
            
    
    def shutterModeCheck(self):
        if mmc.getProperty(DEVICE[0], 'ElectronicShutteringMode')== 'Rolling':
            choice = QtWidgets.QMessageBox.question(self, 'Shutter Mode',
                                                "Running acquisition in Rolling mode ?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                print("Running in Rolling mode")
                self.saveImageSeq() 
            else:
                print('Change mode in the other panel')
        else:
            self.saveImageSeq()
    
    def saveImageSeq(self):
        name = window.name.text()  ## get Name from text area
        duration = self.dur.value()*1000 ## get duration from spinbox and converted it in ms
        ledRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] # [r,g,b]## get LED ratio
        maxFrames = int(self.framesPerFileLabel.text())
        intervalMs = self.intervalMs.value()
        
        #If abort button was hit, enable execution again, and exit.is_set() will return False (cf sequAcq fct)
        exit.clear()
        
        #Initialise sequence acqu
        (ledList, nbFrames) = sequenceInit(duration, ledRatio, int(float(mmc.getProperty(DEVICE[0], 'Exposure'))), intervalMs)
        
        #Initialize progressBar
        window.progressBar.setMaximum(nbFrames)        
        
        #Initialize tiffWriter object
        (tiffWriterList,savePath) = tiffWriterInit(name, nbFrames, maxFrames)
        
        if self.ledTrigBox.currentText() == 'Software' :
            #Launch seq acq : carries the images acquisition AND saving
            imageCount = sequenceAcqSoftTrig(mmc, nbFrames, maxFrames, intervalMs, DEVICE[0], ledList, tiffWriterList,labjack,window, app, exit) 
            #multipleSnap(mmc, nbFrames, maxFrames, intervalMs, DEVICE[0], ledList, tiffWriterList,labjack,window, app, exit)
            #imageCount=100
            
            ##### IF ABORTED acquisition --> CHECK WICH .tif are empty and suppress it #####  
            if exit.is_set() and ((nbFrames/maxFrames)>=1): #check if abort fct was called and that ;ultiples .tif were initialized
                print 'Empty .tif suppression ?'
                tiffWriterDel(name, savePath, imageCount, maxFrames, tiffWriterList)
        else :
            print 'LED camera trigger function'
            imageCount = sequenceAcqCamTrig(mmc, nbFrames, maxFrames, intervalMs, DEVICE[0], ledList, tiffWriterList,labjack,window, app, exit)
            
        
        tiffWriterClose(tiffWriterList)
        print 'Acquisition done'
        window.progressBar.setValue(0)
            
    def histo(self):
        (mask, h_h, h_w, pixMaxVal, bin_width, nbins) = histoInit(mmc)
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        mmc.snapImage()
        g = mmc.getImage() #Initialize g
        mmc.startContinuousSequenceAcquisition(1)
        while True:
                if mmc.getRemainingImageCount() > 0:
                    g = mmc.getLastImage()
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
        mmc.stopSequenceAcquisition()
        
    def abortFunc(self):
        "Abort a running acquisition - source : https://stackoverflow.com/questions/25029537/interrupt-function-execution-from-another-function-in-python"
        exit.set() #Interrupt the loop of acquisition
        print 'Acquisition abort properly'
        
    
    def unloadDevices(self):
        mmc.unloadAllDevices()
        print 'all devices UNLOADED'
        return True
    
    def closeEvent(self, event):
        # Close all before closing the main window
        if self.unloadDevices(): # UNLOAD DEVICES befor closing the program
            event.accept() # let the window close
        else:
            event.ignore()
        
    def loadZyla(self):
        DEVICE = camInit(mmc)
        print 'Device ',DEVICE[0],' loaded'
        
        
##Launching everything
if __name__ == '__main__':
    
    """MicroManager Init"""

    mmc = MMCorePy.CMMCore()
    
    """Camera Init"""
    global DEVICE
    DEVICE = camInit(mmc) # TO FIX, give DEVICE at some function only
    
    """Labjack init"""
    global labjack
    labjack = labjackInit()
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

