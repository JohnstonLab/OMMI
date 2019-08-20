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
from saveFcts import saveFrame

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
    

def sequenceInit(duration, ledRatio, exp):
    "Prepare (and DISPLAY??) infos about the sequence acq coming"


    ## Initialize timeStamps
    ## Open a Tiff file ?
    ## send all of this to sequence acq
    intervalMs = (exp+10)           ## Calculation of interval between frames (images)
    nbFrames = int((duration)/intervalMs)+1  ## Determine number of frames. (+1) ensure to have a list long enough
    ledSeq = ['r']*ledRatio[0]+['g']*ledRatio[1]+['b']*ledRatio[2] #Sequence of LED lighting in function of the ratio
    print 'LED sequence : ', ledSeq
    ledList = ledSeq*(int(nbFrames/(len(ledSeq)))+1) ## schedule LED lighting
    return ledList, nbFrames, intervalMs
    

def sequenceAcq(mmc, nbImages, intervalMs, deviceLabel, ledList):
    #Get the time when save button pressed
    timeStamps = []
    timeStamps.append(time())
    #Setting the minimal interval between images?
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
    while(imageCount<(nbImages)): # failure count avoid looping infinitely
        #sleep(0.001*(intervalMs-10)) #Delay in seconds, can be closed to intervalMs to limit loops for nothing
        #CALL TO SAVING FCT (img, expName, num)
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

def sequenceAcq2(mmc, nbImages, intervalMs, deviceLabel, ledList):
    "Prepare and start the sequence acquisition. Write frame in an tiff file during acquisition."
    
    #Get the time ##TO FIX : is it the right place to put it on ?
    timeStamps = []
    timeStamps.append(time())
    #Setting the minimal interval between images?
    print "Interval between images : ", intervalMs,"ms"
    print "Nb of frames : ", nbImages
    mmc.prepareSequenceAcquisition(deviceLabel)
    mmc.startSequenceAcquisition(nbImages, intervalMs, False)   #numImages	Number of images requested from the camera
                                                        #intervalMs	The interval between images, currently only supported by Andor cameras
                                                        #stopOnOverflow	whether or not the camera stops acquiring when the circular buffer is full 
    ## Turn red LED on because frame will always begin by that ?
    failureCount=0
    imageCount =0
    #mmc.startContinuousSequenceAcquisition(10)
    while(imageCount<(nbImages)) & (failureCount<100000): # failure count avoid looping infinitely
        #sleep(0.001*(intervalMs-10)) #Delay in seconds, can be closed to intervalMs to limit loops for nothing
        
        #Launching acquisition
        if mmc.getRemainingImageCount() > 0: #Returns number of image in circular buffer, stop when seq acq finished
                    #Lighting good LED
            if ledList[imageCount] == 'r':
                #print "Blue off" ## Only one LED to turn off because we know the fire order
                print "Red on"  
            elif ledList[imageCount] == 'g':
                print "Green on"
            else:
                print "Blue on"
            sleep(0.005) #Wait 5ms to ensure LEDS are on
            #g = mmc.getLastImage()
            g = mmc.popNextImage() #Gets and removes the next image from the circular buffer
            t=time()
            timeStamps.append(t)
            saveFrame(g)
            imageCount +=1
        else:
            failureCount+=1
            
        ##Save image captured

    print "Failure count = ", failureCount
    #Print the reql interval between images ## Can be done in post-processing with timeStamps
    for i in range(0,len(timeStamps)-2):
        print  "delta time between t",i+1," and t",i," : ",(timeStamps[i+1] -timeStamps[i])
            
    mmc.stopSequenceAcquisition()
    mmc.clearCircularBuffer() 
    
    return timeStamps
