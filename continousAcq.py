# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 09:39:33 2019

@author: Louis Vande Perre

Contains all features with continous camera acquisition.
"""
# Used packages
import cv2

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

####USELESS#### 
def histoLive(mmc, thd , mask):
    cv2.namedWindow('Video')
    mmc.snapImage()
    g = mmc.getImage() #Initialize g
    mmc.startContinuousSequenceAcquisition(1)
    while True:
            if mmc.getRemainingImageCount() > 0:
                g = mmc.getLastImage()
                rgb2 = cv2.cvtColor(g.astype("uint16"),cv2.COLOR_GRAY2RGB)
                rgb2[g>thd]=mask[g>thd]*256
                cv2.imshow('Video', rgb2)
                return g
                    
            else:
                print('No frame')
    return False #No image captured