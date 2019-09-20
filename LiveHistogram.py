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


class LiveHistogram(QThread):
    """
    Class for live histogram object.
    This class is in charge of acquire and display live acquisition, calculate and display a histogram.
    Source for QThread management (inspiration) :  https://nikolak.com/pyqt-threading-tutorial/
                            https://medium.com/@webmamoffice/getting-started-gui-s-with-python-pyqt-qthread-class-1b796203c18c
                                --> https://gist.github.com/WEBMAMOFFICE/fea8e52c8105453628c0c2c648fe618f (source code)
    """
    
    
    def __init__(self, mmc,parent=None):
        QThread.__init__(self,parent)
        self.mmc = mmc
        #Set hist parameters
        self.hist_height = 512
        self.hist_width = 512
        self.nbins = 512 # x axis
        self.bin_width = self.hist_width/self.nbins
        self.pixMaxVal=65536
        print 'basic parameters ok'
        #Create a red mask to display the saturated pixel on this mask
        mask_red = np.ones((self.mmc.getImageHeight(),self.mmc.getImageWidth()),dtype=np.uint8) * 255
        self.mask = np.zeros((self.mmc.getImageHeight(),self.mmc.getImageWidth(),3),dtype=np.uint8)
        self.mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (b,g,r)
        
        print 'Histogram class initiated'
        
        
    def __del__(self):
        self.wait()
        
    def run(self):
        print 'Histogram class launched'
        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        self.mmc.snapImage()
        img = self.mmc.getImage() #Initialize g
        self.mmc.startContinuousSequenceAcquisition(1)
        while True:
                if self.mmc.getRemainingImageCount() > 0:
                    img = self.mmc.getLastImage()
                    rgb2 = cv2.cvtColor(img.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[img>(self.pixMaxVal-2)]=self.mask[img>(self.pixMaxVal-2)]*256 #It cannot be compared to pixMaxVal because it will never reach this value
                    cv2.imshow('Video', rgb2)
                        
                else:
                    print('No frame')
                    
                h = self.histoCalc(img)
                cv2.imshow('Histogram',h)
                
                if cv2.waitKey(33) == 27:
                    break
                if cv2.getWindowProperty('Video', 1) == -1: #Condition verified when 'X' (close) button is pressed
                    break
                elif cv2.getWindowProperty('Histogram', 1) == -1: #Condition verified when 'X' (close) button is pressed
                    break

        cv2.destroyAllWindows()
        self.mmc.stopSequenceAcquisition()
        print 'Histogram thread over'
        
#    def _histoInit(self):
#        
#    
#        #Create an empty image for the histogram
#        #h = np.zeros((hist_height,hist_width))
#        mask_red = np.ones((self.mmc.getImageHeight(),self.mmc.getImageWidth()),dtype=np.uint8) * 255
#        self.mask = np.zeros((self.mmc.getImageHeight(),self.mmc.getImageWidth(),3),dtype=np.uint8)
#        self.mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (b,g,r)
#        #return (mask, hist_height, hist_width, pixMaxVal, bin_width, nbins)

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


### TEST SECTION
import MMCorePy
from camInit import camInit

if __name__ == '__main__':
    """MicroManager Init"""
    mmc = MMCorePy.CMMCore()
    print 'mmc init'
    
    """Camera Init"""
    DEVICE = camInit(mmc)
    
    print 'camInit'
    liveHisto = LiveHistogram(mmc)
    liveHisto.start()
