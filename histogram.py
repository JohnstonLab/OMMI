# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 16:27:27 2019

@author: johnstonlab
To describe
"""
import numpy as np
import cv2


def histoInit(mmc):
    #Set hist parameters
    hist_height = 512
    hist_width = 512
    nbins = 512 # x axis
    bin_width = hist_width/nbins
    maxVal=65536 #256

    #Create an empty image for the histogram
    #h = np.zeros((hist_height,hist_width))
    mask_red = np.ones((mmc.getImageHeight(),mmc.getImageWidth()),dtype=np.uint8) * 255
    mask = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint8)
    mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (b,g,r)
    return (mask, hist_height, hist_width, maxVal, bin_width, nbins)


def histoCalc(nbins, pixMaxVal, bin_width, h_h, h_w, g):
    #Calculate, normalize and display the histogram
    #Create an empty image for the histogram
    h = np.zeros(( h_h, h_w))
    hist_g = cv2.calcHist([g],[0],None,[nbins],[0,pixMaxVal])
    hist_height = len(h[0])
    cv2.normalize(hist_g,hist_g,hist_height,cv2.NORM_MINMAX)
    hist=np.uint16(np.around(hist_g))

    #Loop through each bin and plot the rectangle in black
    for x,y in enumerate(hist):
        cv2.rectangle(h,(x*bin_width,y),(x*bin_width + bin_width-1,hist_height),(255),-1)

    #Flip upside down
    h=np.flipud(h)
    return h
    #Show the histogram
    #rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint16)