# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 17:30:36 2019

@author: johnstonlab

Containing Histogram Class
"""
#Packages import
from PyQt5.QtCore import QThread, pyqtSignal
from time import sleep
import numpy as np
import cv2
from multiprocessing.pool import ThreadPool

#Function import
from Labjack import waitForSignal, redOn, redOff, greenOn, greenOff, blueOn, blueOff, trigImage


class LiveHistogram(QThread):
    """
    Class for live histogram object.
    This class is in charge of acquire and display live acquisition, calculate and display a histogram.
    Source for QThread management (inspiration) :  https://nikolak.com/pyqt-threading-tutorial/
                            https://medium.com/@webmamoffice/getting-started-gui-s-with-python-pyqt-qthread-class-1b796203c18c
                                --> https://gist.github.com/WEBMAMOFFICE/fea8e52c8105453628c0c2c648fe618f (source code)
    """
    
    modeChoice = pyqtSignal()
    
    
    def __init__(self, mmc, labjack, parent=None):
        QThread.__init__(self,parent) #Call the parent class constructor
        
        self.mmc = mmc
        self.labjack = labjack
        #Set hist parameters
        self.hist_height = 512
        self.hist_width = 512
        self.nbins = 512 # x axis
        self.bin_width = self.hist_width/self.nbins
        self.pixMaxVal=65536
        self.ledOnDuration = 0.0005
        
        #Create a red mask to display the saturated pixel on this mask
        mask_red = np.ones((self.mmc.getImageHeight(),self.mmc.getImageWidth()),dtype=np.uint8) * 255
        self.mask = np.zeros((self.mmc.getImageHeight(),self.mmc.getImageWidth(),3),dtype=np.uint8)
        self.mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (b,g,r)
        
        #Acquisition parameters
        self.running = True
        self.led =None
        
        
    def __del__(self):
        self.wait()


    def _histoCalc(self, img):
        #Calculate, normalize and display the histogram
        #Create an empty image for the histogram
        h = np.zeros(( self.hist_height, self.hist_width))
        hist_g = cv2.calcHist([img],[0],None,[self.nbins],[0,self.pixMaxVal])
        cv2.normalize(hist_g,hist_g,self.hist_height,cv2.NORM_MINMAX)
        hist=np.uint16(np.around(hist_g))
    
        #Loop through each bin and plot the rectangle in black
        for x,y in enumerate(hist):
            cv2.rectangle(h,(x*self.bin_width,y),(x*self.bin_width + self.bin_width-1,self.hist_height),(255),-1)
    
        #Flip upside down
        h=np.flipud(h)
        return h
        #Show the histogram
        #rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint16)
        
        
            
    def _ledBlinking(self):
        """
        Function in charge of blinking the LED.
        """
        print 'Blinking LED fct'
        while(self.running):
            #Will return only if ARM output signal from the camera raise
            if waitForSignal(self.labjack, "TTL", "AIN", 0): #WaitForSignal return TRUE when AIN0 (ARM output from the camera) input is HIGH (>3V)
                #Lighting good LED for next acquisition
                #trigImage(self.labjack) # Trigger the image --> future improvements, use a basic OR gate to get all the LED signal
                if self.led== 'r':
                    redOn(self.labjack)
                    sleep(self.ledOnDuration)
                    redOff(self.labjack)
                elif self.led == 'g':
                    greenOn(self.labjack)
                    sleep(self.ledOnDuration)
                    greenOff(self.labjack)
                elif self.led == 'b':
                    blueOn(self.labjack)
                    sleep(self.ledOnDuration)
                    blueOff(self.labjack)
                else:
                    trigImage(self.labjack)
                    
    def _histoDisplaying(self):
        """
        Function in charge of acquiring the frame and displaying the histogram.
        """
        print 'Displaying frame fct'
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        self.mmc.startContinuousSequenceAcquisition(1)
        while(self.running):
            try:
                if self.mmc.getRemainingImageCount() > 0:
                    img = self.mmc.getLastImage()
                    rgb2 = cv2.cvtColor(img.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[img>(self.pixMaxVal-2)]=self.mask[img>(self.pixMaxVal-2)]*256 #It cannot be compared to pixMaxVal because it will never reach this value
                    cv2.imshow('Video', rgb2)
                else:
                    print('No frame')
            except:
                print 'HISTO : MMC acquisition error'
            try:    
                h = self._histoCalc(img)
                cv2.imshow('Histogram',h)
            except:
                print 'HISTO : Calculation of the histogram error'
            if cv2.waitKey(33) == 27:
                self.running = False #Stop the acquisition and LED blinking
                break
            if cv2.getWindowProperty('Video', 1) == -1: #Condition verified when 'X' (close) button is pressed
                self.running = False #Stop the acquisition and LED blinking
                break
            elif cv2.getWindowProperty('Histogram', 1) == -1: #Condition verified when 'X' (close) button is pressed
                self.running = False #Stop the acquisition and LED blinking
                break
        cv2.destroyAllWindows()
        self.mmc.stopSequenceAcquisition()
        self.mmc.clearCircularBuffer()

    def blinkingLedMode(self):
        print 'Blinking LED'
        pool = ThreadPool(processes=2)
        print 'Pool initialized'
        ledOnDuration=0.005
        
        frameSavingThread = pool.apply_async(self._histoDisplaying,())
        sleep(0.005) ## WAIT FOR INITIALIZATION AND WAITFORSIGNAL FCT
        ledSwitchingThread = pool.apply_async(self._ledBlinking,())
        
        #close the pool and wait for the work to finish
        pool.close()
        pool.join()
        
    def continousLedMode(self):
        print 'old histogram version'
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        self.mmc.snapImage()
        img = self.mmc.getImage() #Initialize g
        self.mmc.startContinuousSequenceAcquisition(1)
        while True:
            try:
                if self.mmc.getRemainingImageCount() > 0:
                    img = self.mmc.getLastImage()
                    rgb2 = cv2.cvtColor(img.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[img>(self.pixMaxVal-2)]=self.mask[img>(self.pixMaxVal-2)]*256 #It cannot be compared to pixMaxVal because it will never reach this value
                    cv2.imshow('Video', rgb2)
                else:
                    print('No frame')
            except:
                print 'HISTO : MMC acquisition error'
            try:    
                h = self._histoCalc(img)
                cv2.imshow('Histogram',h)
            except:
                print 'HISTO : Calculation of the histogram error'
            if cv2.waitKey(33) == 27:
                break
            if cv2.getWindowProperty('Video', 1) == -1: #Condition verified when 'X' (close) button is pressed
                break
            elif cv2.getWindowProperty('Histogram', 1) == -1: #Condition verified when 'X' (close) button is pressed
                break
        cv2.destroyAllWindows()
        self.mmc.stopSequenceAcquisition()
    
    def run(self):
        print 'running thread'
        self.modeChoice.emit()
        
        

