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
trig = 7    #FIO7

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
    
def greenOff(device):
    #print "green OFF"
    device.setFIOState(green_lj, 0)

def redOn(device):
    #print "red ON"
    device.setFIOState(red_lj, 1)
    
def redOff(device):
    #print "red OFF"
    device.setFIOState(red_lj, 0)

def trigExposure(device, exp):
    device.setFIOState(trig, 1)
    sleep(exp*0.001) #milliseconds conversion
    device.setFIOState(trig, 0)
    
def trigImage(device):
    device.setFIOState(trig, 1)
    sleep(0.00001) #minimum required trig is 8 ns
    device.setFIOState(trig, 0)

##CHECK ARM output of the cam is high


#print 'trig Exposure test'
#device = labjackInit()
#exp = 50
#for i in range(0,100):
#    trigExposure(device,exp)
#    sleep(0.025)
    ###GIVES A GOOD SQUARE WAVE (30ms between wave instead of 25.. maybe the loop)