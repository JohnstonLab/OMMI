# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 16:48:18 2019

@author: johnstonlab
"""

import u3


#red/green leds
toggle_r=False
toggle_g=False
red_lj=5
green_lj=4

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
        print "open error" # TO FIX : adapt error msg
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