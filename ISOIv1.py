# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 10:46:56 2019

@author: Louis Vande Perre

Main file of ISOI software.
v1 using the demo cam from MM

TASK :
    1. Display live acquisition to set camera settings
    2. Save a series of images
    
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
from liveFunc import liveFunc


########## GLOBAL VAR - needed for displays information ######

#trackbar
div=100
step=1/float(div)

#Exposure (just here to keep it as global var)
exp=2
expMin=0.0277
expMax=500

#DEVICE to load - Label, description, Name
DEVICE = ['Camera', 'DemoCamera', 'DCam']
#DEVICE = ['Zyla','AndorSDK3','Andor sCMOS Camera']

mmc = MMCorePy.CMMCore()  # Instance micromanager core

# Demo camera example, connections non mandatory
mmc.loadDevice(*DEVICE)
mmc.initializeAllDevices()
mmc.setCameraDevice(DEVICE[0])

class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('isoi_window.ui', self)
        
        # Connect buttons 
        self.liveBtn.clicked.connect(self.liveFunc)
        self.cropBtn.clicked.connect(self.crop)
        self.histoBtn.clicked.connect(self.Histo)
        
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
        self.expSlider.setValue(exp)  
        self.expSlider.valueChanged.connect(self.expFunc)
        
        #spinbox
        self.C_expSb.setMaximum(expMax)
        self.C_expSb.setMinimum(expMin)
        self.C_expSb.setValue(exp)
        self.C_expSb.valueChanged.connect(self.expFunc)
        self.C_expSb.setSingleStep(float(step))
        
        
    def liveFunc(self):
        cv2.namedWindow('Video - press any key to close') #open a new window
        mmc.startContinuousSequenceAcquisition(1) #acquisition each 1 ms, images put in circular buffer
        while True:
                if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer
                    g = mmc.getLastImage()
                    cv2.imshow('Video - press any key to close', g)
                else:
                    print('No frame')
                if cv2.waitKey(32) >= 0:
                    break
        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()
        
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
            
    def Histo(self):
        print "press q to quit"
        #Initialize the windows used to display live video and histogram
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        
        #Set hist parameters
        hist_height = 512
        hist_width = 512
        nbins = 512 # x axis
        bin_width = hist_width/nbins
        
        #threshold red mask, saturated pixels
        thd=65500
        
        range_g=65536 #256

        #Create an empty image for the histogram
        h = np.zeros((hist_height,hist_width))
        rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint8)
        mask_red = np.ones((mmc.getImageHeight(),mmc.getImageWidth()),dtype=np.uint8) * 255
        mask = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint8)
        mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (b,g,r)

        
        mmc.snapImage()
        g = mmc.getImage() #Initialize g
        mmc.startContinuousSequenceAcquisition(1)
        while True:
                if mmc.getRemainingImageCount() > 0:
                    g = mmc.getLastImage()
                    rgb2 = cv2.cvtColor(g.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[g>thd]=mask[g>thd]*256
                    cv2.imshow('Video', rgb2)
                        
                else:
                    print('No frame')
                if cv2.waitKey(32) >= 0:
                    break
                
                
                #Calculate and normalise the histogram
                hist_g = cv2.calcHist([g],[0],None,[nbins],[0,range_g])
                cv2.normalize(hist_g,hist_g,hist_height,cv2.NORM_MINMAX)
                hist=np.uint16(np.around(hist_g))
        
                #Loop through each bin and plot the rectangle in white
                for x,y in enumerate(hist):
                    cv2.rectangle(h,(x*bin_width,y),(x*bin_width + bin_width-1,hist_height),(255),-1)
        
                #Flip upside down
                h=np.flipud(h)
        
                #Show the histogram
                cv2.imshow('Histogram',h)
                h = np.zeros((hist_height,hist_width))
                #rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint16)
          
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the loop
                if key == ord("q"):
                    break

        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()
        
##Launching everything
if __name__ == '__main__':
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow() 
    window.show()
    sys.exit(app.exec_())

