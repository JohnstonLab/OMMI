# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 09:39:33 2019

@author: Louis Vande Perre

Contains all features with continous camera acquisition.
"""
# Used packages
import cv2
from time import sleep, time

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
    #Get the time when save button pressed
    timeStamps = []
    timeStamps.append(time())
    #Setting the minimal interval between images
    exp = int(float(mmc.getProperty(deviceLabel, 'Exposure')))
    intervalMs = (exp+10) #TO FIX --> how this value can be approx ?
    print "Interval between images : ", intervalMs,"ms"
    #Initialize frame list that will contain all images snapped
    frames=[]
    mmc.prepareSequenceAcquisition(deviceLabel)
    mmc.startSequenceAcquisition(nbImages, intervalMs, False)   #numImages	Number of images requested from the camera
                                                        #intervalMs	The interval between images, currently only supported by Andor cameras
                                                        #stopOnOverflow	whether or not the camera stops acquiring when the circular buffer is full 
    
    failureCount=0
    imageCount =0
    #mmc.startContinuousSequenceAcquisition(10)
    while(imageCount<(nbImages)) & (failureCount<10000): # failure count avoid looping infinitely
        sleep(0.001*exp) #Delay in seconds, can be closed to intervalMs to limit loops for nothing
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished
            #g = mmc.getLastImage()
            g = mmc.popNextImage() #Gets and removes the next image from the circular buffer
            frames.append(g)
            timeStamps.append(time())
            imageCount +=1
        else:
            #print('No frame')
            failureCount+=1
    print "Failure count = ", failureCount
    #Print the reql interval between images ## Can be done in post-processing with timeStamps
    for i in range(0,len(timeStamps)-2):
        print  "delta time between t",i+1," and t",i," : ",(timeStamps[i+1] -timeStamps[i])
            
    mmc.stopSequenceAcquisition()
    mmc.clearCircularBuffer() 
    
    return timeStamps, frames
