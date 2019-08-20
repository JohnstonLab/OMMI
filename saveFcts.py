# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 13:59:59 2019

@author: Louis Vande Perre

Please set savePath.
This file contains all saving-related functions.
"""
import numpy as np
from tifffile import imsave
from datetime import date
import os

date = str(date.today())
savePath="C:/data_OIIS/"+date[2:4]+date[5:7]+date[8:10]

if not os.path.exists(savePath):
    os.makedirs(savePath)

def saveImage(mmc):
      mmc.snapImage()
      img = mmc.getImage()
      imsave('test.tif', img)
      
def saveAsMultipageTifPath(datap,namep,datatype,k):
    #k -> number of page per tif
    # S L O W 
    
    try:
        if datatype == None:
            datatype=datap.dtype
    except:
        print("datatype "+str(datatype))
    
    nFrames=datap.shape[0] #.shape returns the dimensions of the array (rows, columns)
    
    #os.path.split(path)[1]+'_' #get the name of the subfolder
    n=0 #initialize var    ​
    for i in range(0,int(nFrames/k)):
        print("file "+str(i))
        image = datap[i*k:(i*k)+k,:,:]
        filename = savePath+"/"+namep+'%(number)04d.tif' % {"number": i} #%04d return a 4 char string : 1-->0001
        imsave(filename, image.astype(datatype))
        n=i
        
    if (nFrames % k > 0 ):
        print("last file")
        image = datap[nFrames-(nFrames % k):nFrames] ###fixed -1]
        filename = savePath+"/"+namep+'%(number)04d.tif' % {"number": n+1}
        imsave(filename, image.astype(datatype))                                                                                                                                                                                                                                                        

def saveFrame(img):
    print "im saved"