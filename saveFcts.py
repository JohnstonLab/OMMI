# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 13:59:59 2019

@author: Louis Vande Perre

Please set savePath.
This file contains all saving-related functions.
"""

#from __future__ import division ## Allows / to divide float (and give a float number in result)
import numpy as np
import tifffile
from tifffile import imsave, imread
from datetime import date
import json
import os
import fnmatch
from datetime import datetime
import threading


    
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

def saveFrame(img, tiffWriterList, imageCount, maxFrames):
    ## SOURCE : https://stackoverflow.com/questions/20529187/what-is-the-best-way-to-save-image-metadata-alongside-a-tif-with-python
    ## TAGS list : https://github.com/blink1073/tifffile/blob/master/tifffile/tifffile.py#L5000
    ## Tags plugins : https://imagej.nih.gov/ij/plugins/tiff-tags.html
    ## METADATA types : https://github.com/blink1073/tifffile/blob/master/tifffile/tifffile.py#L7749
    ## Metadata plugin : https://imagej.nih.gov/ij/plugins/metadata/MetaData.pdf
    #metadata = dict(microscope='george', shape=img.shape, dtype=img.dtype.str)
    #metadata = json.dumps(metadata)
    #extra_tags = [(270, 's', 0, str(datetime.now()), False)] #[(code, dtype, count, value, writeonce)] #306 = DateTime
               
    
    tiffWriterList[imageCount/maxFrames].save(img) #Remember : / is an integer division, return an integer
    if((imageCount+1)%maxFrames == 0): #If the file is complete, nb frames = max frames (!imageCount start at 0!)  
        print 'There is a .tif file to close - time :', datetime.now()
        tifToClose =tiffWriterList[((imageCount+1)/maxFrames)-1] # goal : to close the completed tif, ensure that frames are saved in case of crash
        thread1 = threading.Thread(target=tiffClose, args=(tifToClose,))
        #https://stackoverflow.com/questions/15085348/what-is-the-use-of-join-in-python-threading
        thread1.setDaemon(True) #Daemonized thread 'ignores' lifetime of other threads - no more delay
        thread1.start()
    #Write LED and timestamp in metadata"

def saveMetadata(textFile, time, led, imageCount, odourValveSig, respirationSig, ledOnDuration): 
    """
    Save the metadata of each frame in a given .txt file.
    Each line of the .txt file corresponds to an image and the metadatas are 
    separated by a tab space.
    """
    textFile.write(time+'\t'+led+'\t'+imageCount+'\t'+odourValveSig+'\t'+respirationSig+'\t'+ledOnDuration+'\n')


def cfgFileSaving(name, nbFrames, duration, ledIllumRatio, ledTriggerMode, 
                  ledSwitchingMode, rgbLedRatio, greenFrameInterval, framerate, 
                  folderPath,colorMode, mmc, deviceLabel):
    """
    Save the experiment configuration parameters in a JSON file.
    """
    print 'initializing folder'
#    today = str(date.today())
#    '/'+today[2:4]+today[5:7]+today[8:10]+
    savePath=folderPath+"/"+name
    
    #Checking if a folder already exist for the experiments of the day
    if not os.path.exists(savePath):
        os.makedirs(savePath)
    print 'Saving configuration file'
    #Create a Python dictionary with all the informations
    
    
    experimentConfiguration = {
            "Global informations":{
                    "Experiment date and time":str(datetime.now()),         #str
                    "Experiment name":name,                                 #str
                    "Number of frames":nbFrames,                            #int or NoneType
                    "Duration":duration                                    #float
            },
            ### Acquisition settings ###
            "Acquisition settings":{
                    "LED illumination time (% of exposure)":ledIllumRatio,    #float
                    "LED trigger mode":ledTriggerMode,                      #str
                    "LED switching mode":ledSwitchingMode,                  #str
                    "(RGB) LED ratio":rgbLedRatio,                          #list of int
                    "(RB) Color(s)":colorMode,                              #str
                    "(RB) Green frames interval":greenFrameInterval,          # int
                    "Tested framerate": framerate                           #float
            },
            
            ### Camera settings ###
            "Camera settings" :{
                    "Exposure":mmc.getExposure(),                                           #double
                    "Bit depth":mmc.getProperty(deviceLabel,'Sensitivity/DynamicRange'),    #str
                    "Binning":mmc.getProperty(deviceLabel,'Binning'),                       #str   
                    "Shutter mode":mmc.getProperty(deviceLabel, 'ElectronicShutteringMode'),#str
                    "Trigger mode":mmc.getProperty(deviceLabel, 'TriggerMode'),             #str
                    "Overlap mode":mmc.getProperty(deviceLabel, 'Overlap'),                 #str
                    "ROI": mmc.getROI(),                                                    #list of int
                    "Pixel readout rate":mmc.getProperty(deviceLabel,'PixelReadoutRate')    #str
            }
    }
    print 'Saving in JSON format'
    with open(savePath+"/"+name+"CFG.json", 'w') as outfile:
        json.dump(experimentConfiguration, outfile)
        outfile.close()
    print 'saving succeed'
    return savePath
    
def jsonFileLoading(filePath):
    """
    Open a json file and create a python dictionnary.
    """
    pyDict = None
    try:
            with open(filePath) as json_file:
                pyDict = json.load(json_file)
    except:
            print 'error in loading the file'
    return pyDict

def filesInit(savePath, name, nbFrames, maxFrames):
    """
    Initialize the right number of .tif files to save the frames.
    Initialize a .txt file to save metadata related to each frame.
    """
    #Initiate a list of TiffWriter object (one per file)    
    tifList=[]
    if ((nbFrames%maxFrames) > 0 ): ##checking if nbFrames/maxFrames returned an int
        for i in range(0,int(nbFrames/maxFrames)+1):
            filename = savePath+"/"+name+'%(number)04d.tif' % {"number": i+1} #%04d return a 4 char string : 1-->0001
            tif = tifffile.TiffWriter(filename) #See tifffile.py for others param 
            tifList.append(tif)
    else:
        for i in range(0,(nbFrames/maxFrames)):
            filename = savePath+"/"+name+'%(number)04d.tif' % {"number": i+1} #%04d return a 4 char string : 1-->0001
            tif = tifffile.TiffWriter(filename) #See tifffile.py for others param 
            tifList.append(tif)
    print len(tifList),' Tif(s) initiated'
    
    #Inititate a .txt file where the metadata will be written
    textFile = open(savePath+"/"+name+".txt", 'w')
    
    return (tifList, textFile)


def emptyTiffDel(name, savePath, imageCount, maxFrames, tiffWriterList):
    """
    Supress the empty tiff generated for an aborted sequence acquisition.
    """
    for i in range((imageCount/maxFrames)+1,len(tiffWriterList)):   #All files that are empty (imageCount/maxFrames)+1, will be suppressed
        filename = savePath+"/"+name+'%(number)04d.tif' % {"number": i+1}
        try:
            os.remove(filename)
            print 'Empty .tif suppression succeed'
        except OSError as e:  ## if failed, report it back to the user ##
            print ("Error: %s - %s." % (e.filename, e.strerror))


def acqFilesDel(fileBaseName, filesPath):
    """
    Suppres all the file with the basename took in argument.
    """
    
    for file in os.listdir(filesPath):
        if fnmatch.fnmatch(file, fileBaseName+'*'):
            try:    
                os.remove(filesPath+'/'+file)
                print (file+' suppression succeed')
            except OSError as e:  ## if failed, report it back to the user ##
                print ("Error: %s - %s." % (e.filename, e.strerror))

def tiffWritersClose(tifList):
    for tif in tifList:
        tif.close()
        print 'tif closed'
        
def tiffClose(tif):
    tif.close()
    print 'tif closed at time : ', datetime.now()


def fileSizeCalculation(framePerFile, ROI, bitDepth):
    print 'xSize : ',ROI[-2],'and ySize : ', ROI[-1]
    nbPix = ROI[-1]*ROI[-2] #(horizontal nb of pix) * (vertical nb of pix), last objects of ROI list
    frameSize = nbPix*bitDepth #in bits
    frameSize = float(frameSize)/(8*1e9) #in gigabytes
    print 'One frame size in GB : ', frameSize
    sizeMax = frameSize*framePerFile
    return round(sizeMax,2)