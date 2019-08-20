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

#Function import

from crop import crop_w_mouse
from histogram import histoInit, histoCalc
from continousAcq import grayLive, sequenceAcq, sequenceInit
from camInit import camInit
from saveFcts import tiffWriterInit, tiffWriterClose
from Labjack import labjackInit, greenOn, greenOff, redOn, redOff


########## GLOBAL VAR - needed for displays information ######

#trackbar
div=100
step=1/float(div)

#Exposure (just here to keep it as global var)
expMin=0.0277
expMax=500

#LEDs Ratio
ratioMax=10
ratioMin=0

class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('isoi_window.ui', self)
        
        # Connect buttons 
        self.liveBtn.clicked.connect(self.liveFunc)
        self.cropBtn.clicked.connect(self.crop)
        self.histoBtn.clicked.connect(self.histo)
        self.SaveEBtn.clicked.connect(self.saveImageSeq)
        
        #ComboBoxes
        self.binBox.addItem("1x1","1x1")
        self.binBox.addItem("2x2","2x2")
        self.binBox.addItem("4x4","4x4")
        self.binBox.addItem("8x8","8x8")
        self.bitBox.addItem("12-bit (high well capacity)","12-bit (high well capacity)")
        self.bitBox.addItem("12-bit (low noise)","12-bit (low noise)")
        self.bitBox.addItem("16-bit (low noise & high well capacity)","16-bit (low noise & high well capacity)")
        self.binBox.setCurrentText(mmc.getProperty(DEVICE[0], 'Binning'))
        self.bitBox.setCurrentText(mmc.getProperty(DEVICE[0], 'Sensitivity/DynamicRange'))
        self.binBox.currentIndexChanged.connect(self.binCh)
        self.bitBox.currentIndexChanged.connect(self.bitCh)
        
        
        # Sliders
        self.expSlider.setMinimum(expMin)
        self.expSlider.setMaximum(expMax)
        self.expSlider.setValue(float(mmc.getProperty(DEVICE[0], 'Exposure')))  
        self.expSlider.valueChanged.connect(self.expFunc)
        
        #### Spinboxes ###
        
        #Exposure
        self.C_expSb.setMaximum(expMax)
        self.C_expSb.setMinimum(expMin)
        self.C_expSb.setValue(float(mmc.getProperty(DEVICE[0], 'Exposure')))
        self.C_expSb.valueChanged.connect(self.expFunc)
        self.C_expSb.setSingleStep(float(step))
        
        #Experiment duration
        self.dur.setSingleStep(float(step))
        
        #LEDs ratios
        self.gRatio.setMinimum(ratioMin)
        self.rRatio.setMinimum(ratioMin)
        self.bRatio.setMinimum(ratioMin)
        self.gRatio.setMaximum(ratioMax)
        self.rRatio.setMaximum(ratioMax)
        self.bRatio.setMaximum(ratioMax)
        
        #####
        
        #Name text area
        self.name.insert("DefaultName")
        
        #LEDs toggle buttons
        self.Green.stateChanged.connect(self.green)
        self.Red.stateChanged.connect(self.red)
        
    def liveFunc(self):
        grayLive(mmc)
        
    def crop(self):
        mmc.clearROI()
        mmc.snapImage()
        img = mmc.getImage()
        (x,y,w,h) = crop_w_mouse(img)
        mmc.setROI(x,y,w,h)
        print "image width: "+str(mmc.getImageWidth())
        print "image height: "+str(mmc.getImageHeight())
        cv2.destroyAllWindows()
    
    def expFunc(self, expVal):
        #exp=expVal/float(div)
        self.C_expSb.setValue(expVal) #update spinbox value
        self.expSlider.setValue(expVal) #update slider value
        try:
            mmc.setProperty(DEVICE[0], 'Exposure', expVal)
        except:
            print "CMM err, no possibility to set exposure"
            
    def binCh(self):
        binn = self.binBox.currentText()
        mmc.setProperty(DEVICE[0], 'Binning', str(binn))
        print "Binning set at", mmc.getProperty(DEVICE[0],'Binning') 

    def bitCh(self):
        bit = self.bitBox.currentText()
        mmc.setProperty(DEVICE[0], 'Sensitivity/DynamicRange', str(bit))
        print "Bit depth set at", mmc.getProperty(DEVICE[0],'Sensitivity/DynamicRange')
    
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

        
    def saveImageSeq(self):
        name = window.name.text()  ## get Name from text area
        duration = self.dur.value()*1000 ## get duration from spinbox and converted it in ms
        ledRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] # [r,g,b]## get LED ratio
        
        #Initialize tiffWriter object
        tiffWriter = tiffWriterInit(name)
        
        #Initialise sequence acqu
        (ledList, nbFrames, intervalMs) = sequenceInit(duration, ledRatio, int(float(mmc.getProperty(DEVICE[0], 'Exposure'))))
        
        #Launch seq acq
        sequenceAcq(mmc, nbFrames, intervalMs, DEVICE[0], ledList, tiffWriter,labjack) #Carries the images acquisition AND saving
        
        #Close tif file where tiffWriter object wrote
        tiffWriterClose(tiffWriter)
        
        print 'Acquisition done'
            
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
                
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the loop
                if key == ord("q"):
                    break

        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()

        
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

