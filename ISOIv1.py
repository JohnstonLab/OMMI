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
from continousAcq import grayLive, sequenceAcq, sequenceInit, sequenceAcq2
from camInit import camInit
from saveFcts import saveImage, saveAsMultipageTifPath, tiffWriterInit, tiffWriterClose


########## GLOBAL VAR - needed for displays information ######

#trackbar
div=100
step=1/float(div)

#Exposure (just here to keep it as global var)
expMin=0.0277
expMax=500

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

        # Sliders
        self.expSlider.setMinimum(expMin)
        self.expSlider.setMaximum(expMax)
        self.expSlider.setValue(float(mmc.getProperty(DEVICE[0], 'Exposure')))  
        self.expSlider.valueChanged.connect(self.expFunc)
        
        #spinbox
        self.C_expSb.setMaximum(expMax)
        self.C_expSb.setMinimum(expMin)
        self.C_expSb.setValue(float(mmc.getProperty(DEVICE[0], 'Exposure')))
        self.C_expSb.valueChanged.connect(self.expFunc)
        self.C_expSb.setSingleStep(float(step))
        
        
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
            
    def saveImage(self): #Not connected to any button
        saveImage(mmc)
        
    def saveImageSeq(self):
        name = 'Exp1'## get Name from text area
        duration = 1*1000 ## get duration from text area (Warning, conversion in ms)
        ledRatio = [8,1,1] # [r,g,b]## get LED ratio
        
        #Initialize tiffWriter object
        tiffWriter = tiffWriterInit(name)
        
        #Initialise sequence acqu
        (ledList, nbFrames, intervalMs) = sequenceInit(duration, ledRatio, int(float(mmc.getProperty(DEVICE[0], 'Exposure')))) 
        #Initialise saving file ?
        #TO DO
        #Launch seq acq
        sequenceAcq2(mmc, nbFrames, intervalMs, DEVICE[0], ledList, tiffWriter)
        tiffWriterClose(tiffWriter)
        #print "Number of frames : ", len(frames)
        #namep=self.path.text()
        #framesnp=np.asarray(frames)
        #saveAsMultipageTifPath(framesnp,"defaultName" ,None, 1024)
        #print "Sequence saved"
            
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
    
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow() 
    window.show()
    sys.exit(app.exec_())

