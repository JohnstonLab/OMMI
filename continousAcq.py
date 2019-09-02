# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 09:39:33 2019

@author: Louis Vande Perre

Contains all features with continous camera acquisition.
IDEA : create a sequence class, in this way, sequence param can be saved when init sequ.
"""
# Used packages
import cv2
from time import sleep, time
from saveFcts import saveFrame, tiffWriterClose
from Labjack import greenOn, greenOff, redOn, redOff, trigImage

def grayLive(mmc):
    cv2.namedWindow('Video - press esc to close') #open a new window
    mmc.startContinuousSequenceAcquisition(1) #acquisition each 1 ms, images put in circular buffer
    while True:
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer
            g = mmc.getLastImage()
            cv2.imshow('Video - press esc to close', g)
        else:
            print('No frame')
        if cv2.waitKey(33) == 27:
            break
        if cv2.getWindowProperty('Video - press esc to close', 1) == -1: #Condition verified when 'X' (close) button is pressed
            break
    cv2.destroyAllWindows()
    mmc.stopSequenceAcquisition()
    

def sequenceInit(duration, ledRatio, exp, intervalMs):
    "Prepare (and DISPLAY??) infos about the sequence acq coming"
    readOutFrame = 10 #ms ##Minimal time between 2 frames (cf page 45 zyla hardware guide)
    ## send all of this to sequence acq
    nbFrames = int((duration)/(intervalMs+readOutFrame+exp))+1  ## Determine number of frames. (+1) ensure to have a list long enough
    ledSeq = ['r']*ledRatio[0]+['g']*ledRatio[1]+['b']*ledRatio[2] #Sequence of LED lighting in function of the ratio
    print 'LED sequence : ', ledSeq
    ledList = ledSeq*(int(nbFrames/(len(ledSeq)))+1) ## schedule LED lighting
    return ledList, nbFrames

def sequenceAcqSoftTrig(mmc, nbImages, maxFrames, intervalMs, deviceLabel, ledList, tiffWriterList, labjack, window, app, exit):
    "Prepare and start the sequence acquisition. Write frame in an tiff file during acquisition."
    
    readOutFrame = 10 #ms ##Minimal time between 2 frames (cf page 45 zyla hardware guide)
    
    #Get the time ##TO FIX : is it the right place to put it on ?
    timeStamps = []
    #timeStamps.append(time()) #Useless to have a timestamp here
    #exp = mmc.getProperty(deviceLabel,'Exposure')
    print "Interval between images : ", (intervalMs+readOutFrame),"ms"
    print "Nb of frames : ", nbImages
    
    #mmc.startContinuousSequenceAcquisition(1)
    imageCount =0
    
    #Initialize the good LED for first image
    if ledList[imageCount] == 'r':
        #print "Blue off"
        greenOff(labjack)
        redOn(labjack)
    elif ledList[imageCount] == 'g':
        redOff(labjack)
        greenOn(labjack)
    else:
        redOff(labjack)
        greenOff(labjack)
        
    #mmc.prepareSequenceAcquisition(deviceLabel)
    #mmc.startSequenceAcquisition(nbImages, intervalMs, False)   #numImages	Number of images requested from the camera
                                                        #intervalMs	The interval between images, currently only supported by Andor cameras
                                                        #stopOnOverflow	whether or not the camera stops acquiring when the circular buffer is full 
    mmc.startContinuousSequenceAcquisition(intervalMs+readOutFrame)
    timeStamps.append(time())

    while(imageCount<(nbImages) and not exit.is_set()): #Loop stops if we have the number of frames wanted OR if abort button is press (see abortFunc)
        #sleep(0.001*(intervalMs-10)) #Delay in seconds, can be closed to intervalMs to limit loops for nothing
        
        #Launching acquisition
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished #Enter this loop BETWEEN acquisition
            #trigImage(labjack) #Generate a pulse, which allows to flag the entry in this code statement with the oscilloscope
            imageCount +=1
            #Lighting good LED for next acquisition
            if ledList[imageCount] == 'r':
                #print "Blue off"
                greenOff(labjack)
                redOn(labjack)
            elif ledList[imageCount] == 'g':
                redOff(labjack)
                greenOn(labjack)
            else:
                redOff(labjack)
                greenOff(labjack)
            #sleep(0.005) #Wait 5ms to ensure LEDS are on
            img = mmc.popNextImage() #Gets and removes the next image from the circular buffer
            timeStamps.append(time())
            saveFrame(img, tiffWriterList, (imageCount-1), ledList[(imageCount-1)], maxFrames) # saving frame of previous acquisition
            window.progressBar.setValue(imageCount) #Update the gui of evolution of the acquisition
            app.processEvents() #Allows the GUI to be responsive even while this fct is executing /!\ check time affection of this skills

    #Turning off all LEDS
    greenOff(labjack)
    redOff(labjack)
    
    #Print the real interval between images ## Can be done in post-processing with timeStamps
    for i in range(0,len(timeStamps)-1):
        print  "delta time between t",i+1," and t",i," : ",(timeStamps[i+1] -timeStamps[i])      
    
    #Close tiff file open
    tiffWriterClose(tiffWriterList)
    
    #Stop camera acquisition
    mmc.stopSequenceAcquisition()
    mmc.clearCircularBuffer() 
    return imageCount



def sequenceAcqCamTrig(mmc, nbImages, maxFrames, intervalMs, deviceLabel, ledList, tiffWriterList, labjack, window, app, exit):
    "Prepare and start the sequence acquisition. Write frame in an tiff file during acquisition. LED triggered by camera output"
    
    readOutFrame = 10 #ms ##Minimal time between 2 frames (cf page 45 zyla hardware guide)
    
    #Get the time ##TO FIX : is it the right place to put it on ?
    timeStamps = []
    #timeStamps.append(time()) #Useless to have a timestamp here
    #exp = mmc.getProperty(deviceLabel,'Exposure')
    print "Interval between images : ", (intervalMs+readOutFrame),"ms"
    print "Nb of frames : ", nbImages
    
    #mmc.startContinuousSequenceAcquisition(1)
    imageCount =0
        
    #mmc.prepareSequenceAcquisition(deviceLabel)
    #mmc.startSequenceAcquisition(nbImages, intervalMs, False)   #numImages	Number of images requested from the camera
                                                        #intervalMs	The interval between images, currently only supported by Andor cameras
                                                        #stopOnOverflow	whether or not the camera stops acquiring when the circular buffer is full 
    mmc.startContinuousSequenceAcquisition(intervalMs+readOutFrame)
    timeStamps.append(time())

    while(imageCount<(nbImages) and not exit.is_set()): #Loop stops if we have the number of frames wanted OR if abort button is press (see abortFunc)
        #sleep(0.001*(intervalMs-10)) #Delay in seconds, can be closed to intervalMs to limit loops for nothing
        
        #Launching acquisition
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished #Enter this loop BETWEEN acquisition
            #trigImage(labjack)
            imageCount +=1
            img = mmc.popNextImage() #Gets and removes the next image from the circular buffer
            timeStamps.append(time())
            saveFrame(img, tiffWriterList, (imageCount-1), ledList[(imageCount-1)], maxFrames) # saving frame of previous acquisition
            window.progressBar.setValue(imageCount) #Update the gui of evolution of the acquisition
            app.processEvents() #Allows the GUI to be responsive even while this fct is executing /!\ check time affection of this skills
    
    #Print the real interval between images ## Can be done in post-processing with timeStamps
    for i in range(0,len(timeStamps)-1):
        print  "delta time between t",i+1," and t",i," : ",(timeStamps[i+1] -timeStamps[i])      
    
    #Close tiff file open
    tiffWriterClose(tiffWriterList)
    
    #Stop camera acquisition
    mmc.stopSequenceAcquisition()
    mmc.clearCircularBuffer() 
    return imageCount


######### EXTERNAL TRIGGER FCTS ##########

def multipleSnap(mmc, nbImages, maxFrames, intervalMs, deviceLabel, ledList, tiffWriterList, labjack, window, app, exit):
    print 'multipleSnap fct'
    cv2.namedWindow('Video')
    for i in range(0,500):    
        mmc.snapImage()
        trigImage(labjack)
        sleep(intervalMs*0.001)
        g = mmc.getImage()
        cv2.imshow('Video', g)
    sleep(5)
    cv2.destroyAllWindows()

def sequenceAcqTriggered(mmc,nbImages, deviceLabel, intervalMs, labjack):
    print "Interval between images : ", intervalMs,"ms"
    print "Nb of frames : ", nbImages
    mmc.prepareSequenceAcquisition(deviceLabel)
    mmc.startSequenceAcquisition(nbImages, intervalMs, False)
    print 'images ready to be taken'
    cv2.namedWindow('Video - wait trigger')
    for i in range(0,10):
        sleep(1)
        print(10-i)
    trigImage(labjack)
    exp = float(mmc.getProperty(deviceLabel, 'Exposure'))
    failureCount=0
    while(failureCount<100):
        sleep(exp*0.001)
        if (mmc.getRemainingImageCount() > 0):
            img = mmc.popNextImage()
            cv2.imshow('Video - wait trigger', img)
        else:
            print 'no frame'
            failureCount+=1
    cv2.destroyAllWindows()
    mmc.stopSequenceAcquisition()
    
