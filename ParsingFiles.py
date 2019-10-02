# -*- coding: utf-8 -*-
"""
Created on Tue Oct 01 11:52:21 2019

@author: Louis Vande Perre

File regrouping all the methods used to parse and analyse the mutlipage .tif
"""

import numpy as np 
import os
import fnmatch
import tifffile

def getNumOfElem(filename,parser="\t"):
    """
    Scan a line in a file and return the number of element per line.
    """
    with open(filename) as f:
        content = f.readlines()
        content = [x.strip() for x in content] 
        #Content is list of all the lines
        #Content[i].split(parser) return a list of the elements in line i
        numOfElem = len(content[0].split(parser))
    return numOfElem

def getNumOfLines(filename):
    """
    Scan a file and return the number of lines.
    """
    lines = 0
    for line in open(filename):
        lines += 1
    return lines

def load2DArrayFromTxt(path,parser="\t"):
    """
    Creat a 2D array from a .txt file.
    """
    numOfLines = getNumOfLines(path)
    numOfElem = getNumOfElem(path,parser)
    arr=np.zeros((numOfLines,numOfElem))

    with open(path) as f:
        content = f.readlines()
        content = [x.strip() for x in content]

    for i in range(numOfLines):
        for j in range(numOfElem):
            
            try:
                arr[i,j]=float(content[i].split(parser)[j])
            except:
                print("Unreadable line "+str(i))
    return arr


def get_immediate_subdirectories(a_dir):
    """
    Return the subdirectories from a folder in a list.
    Source : https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
    """
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
    
def getTifLists(currdir):
    """
    Return a list of the path of all .tif files in the folder.
    """
    tifsList=[]           
    for file in os.listdir(currdir):
        if fnmatch.fnmatch(file, '*.tif'):
            tifsList.append(currdir+"/"+file)
    return tifsList

def splitColorChannel(experimentDir, txtArray, tifsList):
    """
    Takes the metadat and a list of .tif path to create a folder with
    one channel tif and the time stamps corresponding
    """
    #Correction of the txtFile size
    #(Because the metadata and )
    
    
    #Separate infos from the .txt file
    time = txtArray[:,0]
    channel = txtArray[:,1]
    #frames = txtFile[:,2] #Useless
    odourValve = txtFile[:,3] #useless
    #respiration = txtFile[:,4] #useless
    #ledOnDuration =txtFile[:,5] #useless
    
    #Create or verify that processed folder exsits
    savePath = experimentDir+'/Processed'
    if not os.path.exists(savePath):
        os.makedirs(savePath)
    #Create a txt file
    redTextFile = open(savePath+"/"+"red"+".txt", 'w')
    greenTextFile = open(savePath+"/"+"green"+".txt", 'w')
    blueTextFile = open(savePath+"/"+"blue"+".txt", 'w')
    print'.txt init'
    #Create a tiffWriter
    redTif = tifffile.TiffWriter(savePath+"/"+"red"+".tif", bigtiff=True)
    greenTif = tifffile.TiffWriter(savePath+"/"+"green"+".tif", bigtiff=True)
    blueTif = tifffile.TiffWriter(savePath+"/"+"blue"+".tif", bigtiff=True)
    print'.itf init'
    
    splitTifs(redTif, tifsList, 0, channel)
    splitTifs(greenTif, tifsList, 1, channel)
    splitTifs(blueTif, tifsList, 2, channel)
    print'split .tif done'
    
    splitTimestamps(redTextFile, time, odourValve, 0, channel)
    splitTimestamps(greenTextFile, time, odourValve, 1, channel)
    splitTimestamps(blueTextFile, time, odourValve, 2, channel)
    print'split .txt done'
    
    redTextFile.close()
    greenTextFile.close()
    blueTextFile.close()
    
    redTif.close()
    greenTif.close()
    blueTif.close()
    
def txtFileSizeCorrection():
    """
    Because the metadata and the are saved in 2 different threads,
    when an acquisition is aborted we can not ensure that the nb of
    frames are the same per file
    """
    ##TO IMPLEMENT
    #could be useful in case of crash
    print ('Text and tif file size correction')

       
def splitTifs(tiffWriter, tifsList, numChannel, channel):
    """
    Loop through the .tif files and save by channel
    """
    startNb = 0
    nbFrames = 0
    for tif in tifsList:
        with  tifffile.TiffFile(tif) as tif:
            images = tif.asarray() #WARNING EVEN NUMBER OF FRAMES
            
            try :
                startNb += nbFrames
                nbFrames = int(images.shape[0])
                segmentChannel = channel[startNb:startNb+nbFrames]##problem last frame
                toSaveArray = np.nonzero(segmentChannel==numChannel)[0] #We now that it is 1D array
                                                                        #np.nonzero is the same function as np.where
            except:
                print'no access to channel ?'
            try:
                for frameNb in toSaveArray:
                    tiffWriter.save(images[frameNb])
            except:
                print 'error with list'


def splitTimestamps(textFile, time, odourValve, numChannel, channel):
    """
    Create new .txt file with timestamps of each frame.
    """
    try:
        toSaveArray = np.nonzero(channel==numChannel)[0] #We now that it is 1D array
        for frameNb in toSaveArray:
            textFile.write(str(time[frameNb])+'\t'+str(odourValve[frameNb])+'\n')
    except:
        print('Parsing .txt file doesnt work')
        
####TEST SECTION ###
                
#print 'TEST'
##txtArray = load2DArrayFromTxt('C:/data_OIIS/190925/ID709_strong_01pc/ID709_strong_01pc.txt',"\t") #EVEN nb of frames
##txtArray = load2DArrayFromTxt('C:/data_OIIS/191002/ID_test/oddNbOfFrames/oddNbOfFrames.txt',"\t") #Odd nb of frames
#txtArray = load2DArrayFromTxt('C:/data_OIIS/191002/Default_folder_name/Abort/Abort.txt',"\t") #Odd nb of frames 
##txtArray = load2DArrayFromTxt('C:/data_OIIS/191002/Default_folder_name/nonAbort/nonAbort.txt',"\t") #Odd nb of frames    
##tifsPathList = getTifLists('C:/data_OIIS/191002/ID_test/oddNbOfFrames')
#tifsPathList = getTifLists('C:/data_OIIS/191002/Default_folder_name/Abort')
##tifsPathList = getTifLists('C:/data_OIIS/191002/Default_folder_name/nonAbort')
#print('array txt and tif list ok')
##splitColorChannel('C:/data_OIIS/190925/ID709_strong_01pc', txtArray, tifsPathList)
##splitColorChannel('C:/data_OIIS/191002/ID_test/oddNbOfFrames', txtArray, tifsPathList)   
#splitColorChannel('C:/data_OIIS/191002/Default_folder_name/Abort', txtArray, tifsPathList) 
##splitColorChannel('C:/data_OIIS/191002/Default_folder_name/nonAbort', txtArray, tifsPathList)   

    