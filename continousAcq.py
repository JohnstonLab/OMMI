# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 09:39:33 2019

@author: Louis Vande Perre

Contains all features with continous camera acquisition.
"""
# Used packages
import cv2
from time import sleep

def grayLive(mmc):
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
    
def sequenceAcq(mmc, nbImages, deviceLabel):
    
    frames=[]
    #mmc.prepareSequenceAcquisition(deviceLabel)
    #mmc.startSequenceAcquisition(nbImages, 10, False)   #numImages	Number of images requested from the camera
                                                        #intervalMs	The interval between images, currently only supported by Andor cameras
                                                        #stopOnOverflow	whether or not the camera stops acquiring when the circular buffer is full 
    
    
    failureCount=0
    imageCount =0
    mmc.startContinuousSequenceAcquisition(10)
    while(imageCount<nbImages): # (failureCount<1000)
        sleep(0.01) #Delay in seconds (must be in function of the exposure...)
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished
            #g = mmc.getLastImage()
            g = mmc.popNextImage() #Gets and removes the next imag from the circular buffer
            frames.append(g)
            imageCount +=1
        else:
            #print('No frame')
            failureCount+=1
    print "Failure count = ", failureCount
            
    mmc.stopSequenceAcquisition()
    mmc.clearCircularBuffer() 
    
    return frames
