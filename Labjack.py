# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 16:48:18 2019

@author: johnstonlab
"""

import u3
from time import sleep


#Labjack information
red_lj=5    #FIO5
green_lj=4  #FIO4
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
        device
    except:
        #Handle all exceptions here
        print "Error : labjack device non available"
    return device

def greenOn(device):
    #print "green ON"
    device.setFIOState(green_lj, 1)
    
def greenOff(device):
    #print "green OFF"
    device.setFIOState(green_lj, 0)

def redOn(device):
    #print "red ON"
    device.setFIOState(red_lj, 1)
    
def redOff(device):
    #print "red OFF"
    device.setFIOState(red_lj, 0)

#def trigExposure(device, exp):
#    print 'pulse generation'
#    device.setFIOState(trig, 1)
#    sleep(exp*0.001) #milliseconds conversion
#    device.setFIOState(trig, 0)
#    print 'pulse generated'
#    
#def trigImage(device):
#    device.setFIOState(trig, 1)
#    sleep(0.00001) #minimum required trig is 8 ns
#    device.setFIOState(trig, 0)

    
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

##CHECK ARM output of the cam is high

#
#print 'trig Exposure test'
#device = labjackInit()
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
#exp = 50
#for i in range(0,100):
#    trigExposure(device,exp)
#    sleep(0.025)
    ###GIVES A GOOD SQUARE WAVE (30ms between wave instead of 25.. maybe the loop)