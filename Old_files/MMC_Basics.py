# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 09:56:00 2019

@author: johnstonlab
"""
import sys
import MMCorePy
import matplotlib.pyplot as plt
import cv2 as cv
from PyQt5 import QtCore, QtWidgets, QtGui, uic

#trackbar
div=100
#Exposure (just here to keep it as global var)
exp=2
expMin=0.0277
expMax=500


mmc = MMCorePy.CMMCore()  # Instance micromanager core

# Demo camera example, connections non mandatory
mmc.loadDevice('Camera', 'DemoCamera', 'DCam')
mmc.initializeAllDevices()
mmc.setCameraDevice('Camera')

#plt.figure()
#plt.imshow(img, cmap='gray') #Seems to be better to use opencv for image displaying + VIDEO
#plt.show()
#print mmc.getExposure()
#mmc.setExposure(110)
#mmc.snapImage()
#img = mmc.getImage()  # img - it's just numpy array
#print(img)
#cv.imwrite('test_img_exp.jpg', img)
#cv.imshow("image",img)
#cv.waitKey()
#plt.figure()
#plt.imshow(img, cmap='gray') #Seems to be better to use opencv for image displaying + VIDEO
#plt.show()  # And window will appear
##We can get an image with colours
#mmc.setProperty('Camera', 'PixelType', '32bitRGB')  # Change pixel type
#mmc.snapImage()
#rgb32 = mmc.getImage()
#print(rgb32)

class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('mainwindow.ui', self)
        
        # Connect buttons 
        self.pushButton.clicked.connect(self.liveFunc)
        
        # Sliders
        self.horizontalSlider.setMinimum(expMin*div)
        self.horizontalSlider.setMaximum(expMax*div)
        self.horizontalSlider.setValue(exp*div)  
        self.horizontalSlider.valueChanged.connect(self.expSliderFunc)
        
        
    def liveFunc(self):
        print "video button pressed"
        #Image capture and display
        mmc.snapImage()
        img = mmc.getImage()  # img - it's just numpy array
        #print(img)
        cv.imwrite('test_img.jpg', img)
        cv.imshow("image",img)
        cv.waitKey()
        
    def expSliderFunc(self, expVal):
        exp=expVal/float(div)
        print "wanted exp: "+str(exp)
        try:
            mmc.setProperty('Camera', 'Exposure', exp)
            print "actual exp: "+mmc.getProperty('Camera', 'Exposure')
        except:
            print "CMM err"
        
##Launching everything
if __name__ == '__main__':
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow() 
    window.show()
    sys.exit(app.exec_())
