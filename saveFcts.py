# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 13:59:59 2019

@author: Louis Vande Perre

Please set savePath.
This file contains all saving-related functions.
"""
import numpy as np
import tifffile
from tifffile import imsave, imread
from datetime import date
import os

date = str(date.today())
savePath="C:/data_OIIS/"+date[2:4]+date[5:7]+date[8:10]
#savePath="C:/Users/Louis Vande Perre/Documents/Polytech/Stage/Johnston Lab/ISOI Project 2/"+date[2:4]+date[5:7]+date[8:10]

if not os.path.exists(savePath):
    os.makedirs(savePath)
    
#print "Tiffile trial"
#tif = tifffile.TiffWriter('temp.tif', bigtiff=True)
#img1 = imread('test_rgb.tif')
#img2 = imread('test.tif')
#tif.save(img1)
#tif.save(img2)
#tif.close()


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


def saveFrame(img, tiffWriter, imageCount, led):
    tiffWriter.save(img)
    print "im saved"
    
def tiffWriterInit(name):
    filename = savePath+"/"+name+'.tif'
    tif = tifffile.TiffWriter(filename) #See tifffile.py for others param  
    return tif

def tiffWriterClose(tif):
    tif.close()