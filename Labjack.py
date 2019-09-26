# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 16:48:18 2019

@author: johnstonlab
"""

import u3
from time import sleep

##### TEST NEEDED #####
import cv2
from camInit import camInit
import MMCorePy
from multiprocessing.pool import ThreadPool
import matplotlib.pyplot as plt
import threading
import time

#Labjack information
red_lj=5    #FIO5
green_lj=6  #FIO4
blue_lj = 4 #FIO7
trig = 7 #FIO7 #Is high when any LED goes high
cameraTrig_lj = 0    #AIN0


####USELESS###
## Boolean variable that will represent 
## whether or not the arduino is connected
#connected = False

## establish connection to the serial port that your arduino 
## is connected to.
def labjackInit():
    try:
        device = u3.U3() #Open first found U3
    except:
        #Handle all exceptions here
        print "Error : labjack device non available"
    return device

def greenOn(device):
    #print "green ON"
    device.setFIOState(green_lj, 1)
    device.setFIOState(trig, 1)
    
def greenOff(device):
    #print "green OFF"
    device.setFIOState(green_lj, 0)
    device.setFIOState(trig, 0)
    

def redOn(device):
    #print "red ON"
    device.setFIOState(red_lj, 1)
    device.setFIOState(trig, 1)
    
def redOff(device):
    #print "red OFF"
    device.setFIOState(red_lj, 0)
    device.setFIOState(trig, 0)
    
def blueOn(device):
    #print "red ON"
    device.setFIOState(blue_lj, 1)
    device.setFIOState(trig, 1)
    
def blueOff(device):
    #print "red OFF"
    device.setFIOState(blue_lj, 0)
    device.setFIOState(trig, 0)

def trigExposure(device, exp):
    print 'pulse generation'
    device.setFIOState(trig, 1)
    sleep(exp*(0.001) ) #milliseconds conversion
    device.setFIOState(trig, 0)
    print 'pulse generated'
    
def trigImage(device):
    """
    Create a short-time pulse on the %trig output of the labjack.
    Used to trigger an image when camera is in External trigger mode and %trig 
    connected to the TRIGGER input of the camera.
    """
    device.setFIOState(trig, 1)
    device.setFIOState(trig, 0)

    
def waitForSignal(device, signalType="TTL", channelType="FIO", channel=0):
    """
    Wait for a signal into the LabJack
    
    signalType: string, default = "TTL"
        Sets the signal to expect. Currently supported is a +5.0V TTL
        signal.
        
    channelType: string, default = "FIO"
        Sets the type of input channel to listen on. Can be "FIO" 
        (LabJack's digital I/O) or "AIN" (LabJack's analog input).
    
    channel: int, default = 3
        Sets the channel of `channelType` to listen on.
    """
    trigger = False
    if channelType == "FIO": ##Use a DIGITAL input
        while device.getDIState(channel) == 0:
            continue
        trigger = True
        
    elif channelType == "AIN": ####Use a ANALOG input
        #print "WARNING: This might not work as expected, AIN mode still experimental." #NoWay
        if signalType == "TTL":
            targetVoltage = 3
        while (device.getAIN(channel) - targetVoltage) < 0:
            continue
        trigger = True
    else:
        raise "Error: channelType: {wrongType} not recognised".format(wrongType=channelType)
        
    return trigger

def readSignal(device, channel):
    """
    Read a signal coming into the LabJack (AIN)
    
    channel: int, default = 3
        Sets the channel of `channelType` to listen on.
    """
    try:
        sigValue = device.getAIN(channel)
    except:
        print 'Error, no signal coming into the labjack'
    return sigValue

def readOdourValve(device, channel):
    """
    Converted signal read into 1 if valve open (low voltage) or valve close (high voltage)
    """
    valveState=None
    sigValue = readSignal(device, channel)
    if sigValue>2.8:
        valveState=0
    else :
        valveState=1
    return valveState


    
def risingEdge(device):
    """
    Wait for a rising edge (minimum %trigLevel V) into the LabJack AIN0 port (cameraTrig_lj variable)
    
    return True when the risingedge is detected.
    """
    trigLevel = 3
    rEdge = False
    
    #if (device.getAIN(cameraTrig_lj) > trigLevel):
        #print 'High state, cant wait for rising'
    if(device.getAIN(cameraTrig_lj) < trigLevel): # Check that the signal is in low state    
        while (device.getAIN(cameraTrig_lj) < trigLevel): #get out of this loop only when a high state is detected
            continue
        #print 'falling Edge detected'
        rEdge = True
    
    return rEdge
    
def fallingEdge(device):
    """
    Wait for a falling edge (maximum %trigLevel V) into the LabJack AIN0 port (cameraTrig_lj variable)
    
    return True when the risingedge is detected.
    """
    trigLevel = 0.5
    fEdge = False
    
#    if (device.getAIN(cameraTrig_lj) < trigLevel):
#        print 'Low state, cant wait for falling'
    if(device.getAIN(cameraTrig_lj) > trigLevel): # Check that the signal is in high state    
        while (device.getAIN(cameraTrig_lj) > trigLevel): #get out of this loop only when a low state is detected
            continue
        #print 'falling Edge detected'
        fEdge = True
    
    return fEdge

def snapImage(mmc):
    cv2.namedWindow('Image')
    print 'Window open'
    mmc.snapImage()
    g = mmc.getImage()
    cv2.imshow('Image', g)
    sleep(10)
    cv2.destroyAllWindows()

def multiTrig(device, nbImages):
    for i in range(0,nbImages):
        waitForSignal(device, "TTL", "AIN", 0) ##CHECK ARM output of the cam is high
        trigImage(device) ## trig image i
        print 'image ',i,' triggered'

def multiSnap(device, nbImages, mmc, imageList):
    greenOn(device)
    greenOff(device)
    for i in range(0,nbImages):
        print 'inside the for loop'
        start = time.time()
        while(mmc.getRemainingImageCount()<1 and (time.time() - start)<2):
            continue
        #mmc.snapImage()
        print 'snapped'
        #img = mmc.getImage()
        #img = mmc.getLastImage()
        img=mmc.popNextImage()
        print 'got it'
        imageList.append(img) 
        #greenOn(device)
        #greenOff(device)
        print 'image ',i

#### TESTING EXTERNAL TRIGGERING OF THE CAM ####
###Acquisition of 3 frames with one LED on
#print 'trig Exposure test'
#mmc = MMCorePy.CMMCore()
#mmc.unloadAllDevices()
#DEVICE = camInit(mmc) 
#print (mmc.getLoadedDevices())
#print(mmc.getDeviceType('Zyla'))
##print (mmc.getLoadedDevicesOfType('Camera'))
#mmc.unloadAllDevices()

#labjack = labjackInit()
#
#print 'Listening to signal test'
#for i in range (0,30):
#    print 'Trying to read signal : ', readSignal(labjack, 2)
#    sleep(1)
#print 'test done'
#exp = 0.9
#
#mmc.clearCircularBuffer() ## doesn't change anything
#mmc.initializeCircularBuffer()
#trigExposure(labjack,exp) ## trig image 1
#mmc.snapImage() ##WARNING, it takes the timing of exposure
#trigExposure(labjack,exp) ## flag the end of the snap
#g1 = mmc.getImage() ##Warning, it wait the end of transfer
#
#greenOn(labjack)
#trigExposure(labjack,exp) ## trig image 2
#mmc.snapImage()
#trigExposure(labjack,exp) ## flag the end of the snap
#g2 = mmc.getImage()
#trigExposure(labjack,exp) ## flag the end of the get (because of the long delay, it triggers another imaage acquisition)
#greenOff(labjack)
#
### Show all
#plt.figure()
#plt.imshow(g1,cmap="gray")
#plt.show()
#plt.figure()
#plt.imshow(g2,cmap="gray")
#plt.show()
#
##snap 
#sleep(1)
#mmc.snapImage()
#g3 =  mmc.getImage()
#plt.figure()
#plt.imshow(g3,cmap="gray")
#plt.show()

###Acquisition as fast as possible and get&display image after
#trigExposure(labjack,exp) ## trig image 1
#waitForSignal(labjack, "TTL", "AIN", 0)
#greenOn(labjack)
#trigExposure(labjack,exp) ## trig image 2
#waitForSignal(labjack, "TTL", "AIN", 0)
#greenOff(labjack)
#trigExposure(labjack,exp) ## trig image 3
#
###Acquire images
#for i in range(0,2):
#    mmc.snapImage()
#    g1 = mmc.getImage()
#    greenOn(labjack)
#    greenOff(labjack)
#    plt.figure(i)
#    plt.imshow(g1, cmap='gray')
#    plt.show()
#    print 'image ',i

### Same as above but using multi-threads
#nbImages =3
#imageList = []
#thread1 = threading.Thread(target=multiTrig, args=(labjack, nbImages,))
#thread2 = threading.Thread(target=multiSnap, args=(labjack, nbImages, mmc, imageList,))
#pool = ThreadPool(processes=2)
#
##thread1.start()
#async_result1 = pool.apply_async(multiTrig,(labjack, nbImages,))
#sleep(0.0025)
##thread2.start()
#async_result2 = pool.apply_async(multiSnap,(labjack, nbImages, mmc, imageList,))
#
##imageList = async_result2.get()
##thread1.join()
##thread2.join()
#pool.close()
#pool.join()
#greenOn(labjack) #flag the end of threads execution
#sleep(0.002)
#greenOff(labjack) 
#print 'there are ',len(imageList), ' in the list'
#for i in range(0,len(imageList)):
#    plt.figure()
#    print imageList[i].shape
#    plt.imshow(imageList[i], cmap='gray')
#    plt.show()
#
#print 'trig done'
#mmc.unloadAllDevices()

##### TRIGERRING DURING SEQ ACQUISITION

#mmc.startContinuousSequenceAcquisition(1)
#multiTrig(labjack, nbImages)
#multiSnap(labjack, nbImages, mmc, imageList)
#greenOn(labjack) #flag the end of threads execution
#sleep(0.002)
#greenOff(labjack) 
#print 'there are ',len(imageList), ' in the list'
#for i in range(0,len(imageList)):
#    plt.figure()
#    print imageList[i].shape
#    plt.imshow(imageList[i], cmap='gray')
#    plt.show()
#sleep(0.5)
#mmc.stopSequenceAcquisition()
#mmc.unloadAllDevices()
#print 'trig done'

#### Sequ acqu with threads


#mmc.startContinuousSequenceAcquisition(1)
#thread1 = threading.Thread(target=multiTrig, args=(labjack, nbImages,))
#thread2 = threading.Thread(target=multiSnap, args=(labjack, nbImages, mmc, imageList,))
#pool = ThreadPool(processes=2)
#
##thread1.start()
#async_result1 = pool.apply_async(multiTrig,(labjack, nbImages,))
#sleep(0.0025)
##thread2.start()
#async_result2 = pool.apply_async(multiSnap,(labjack, nbImages, mmc, imageList,))
#
##imageList = async_result2.get()
##thread1.join()
##thread2.join()
#pool.close()
#pool.join()
#greenOn(labjack) #flag the end of threads execution
#sleep(0.002)
#greenOff(labjack) 
#print 'there are ',len(imageList), ' in the list'
#for i in range(0,len(imageList)):
#    plt.figure()
#    print imageList[i].shape
#    plt.imshow(imageList[i], cmap='gray')
#    plt.show()
#sleep(0.5)
#mmc.stopSequenceAcquisition()
#mmc.unloadAllDevices()
#print 'trig done'


### RANDOM CODE FOR EXTERNAL TRIGGERING ####

###Using Threads
#cv2.destroyAllWindows()
#pool = ThreadPool(processes=2)
    
#async_result1 = pool.apply_async(snapImage, (mmc,))
#async_result2 = pool.apply_async(trigExposure, (labjack,exp,))

#close the pool and wait for the work to finish
#pool.close()
#pool.join()
#print 'execution done'

### MultipleSnap
#for i in range(0,500):    
#    mmc.snapImage()
#    trigImage(labjack)
#    sleep(intervalMs*0.001)
#    g = mmc.getImage()
#    cv2.imshow('Video', g)
#sleep(5)
#cv2.destroyAllWindows()


###Square wave
#for i in range(0,10):    
#    trigExposure(labjack,exp)
#    print 'count : ', i
#    sleep(0.010)
#    ##GIVES A GOOD SQUARE WAVE (30ms between wave instead of 25.. maybe the loop)

#### TESTING WAITFORSIGNAL FCT #####

#waitForSignal(device, 'TTL', 'AIN', 0)
#nbFrames = 10
#imageCount=0
#while (imageCount<nbFrames):
#    #sleep(0.1)
#    if waitForSignal(device, 'TTL', 'AIN', 0):
#        print 'Trigger received'
#        imageCount+=1
#        
#print 'acquisition done'
