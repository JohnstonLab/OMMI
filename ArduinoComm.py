# -*- coding: utf-8 -*-
"""
Created on Tue Sep 03 11:54:21 2019

@author: johnstonlab

Script containing all fct in relation with arduino communication.

"""

import serial
import time
import struct
import serial.tools.list_ports as lsports

def connectAndBlink():    
    #The function (comports())returns an iterable that yields tuples of three strings:
        ## port name as it can be passed to serial.Serial or serial.serial_for_url()
        ## description in human readable form
        ## sort of hardware ID. E.g. may contain VID:PID of USB-serial adapters.
    portsList = lsports.comports()
    
    #Scan each ports to find the Teensy board (Cyclops' Arduino) and connect to it
    for i in range(0,len(portsList)):
        try:
            print "Trying...",portsList[i][0]
            if 'Teensy' in portsList[i][1]:
                ser = serial.Serial(portsList[i][0], 9600)
                print 'Arduino connected'
                break
            else:
                print 'Wrong port'
                i+=1
        except:
            print "Failed to connect on",portsList[i][0]
            i+=1
    
    
    for i in range(10):
        time.sleep(0.5)
        ser.write(b'H')   # send the byte string 'H'
        time.sleep(0.5)   # wait 0.5 seconds
        ser.write(b'L')   # send the byte string 'L'
    ser.close()
    print 'ser closed'
    
def connect():
    #The function (comports())returns an iterable that yields tuples of three strings:
        ## port name as it can be passed to serial.Serial or serial.serial_for_url()
        ## description in human readable form
        ## sort of hardware ID. E.g. may contain VID:PID of USB-serial adapters.
    portsList = lsports.comports()
    ser=None
    #Scan each ports to find the Teensy board (Cyclops' Arduino) and connect to it
    for i in range(0,len(portsList)):
        try:
            print "Trying...",portsList[i][0]
            if 'Teensy' in portsList[i][1]:
                ser = serial.Serial(portsList[i][0], 9600)
                print 'Arduino connected'
                break
            else:
                print 'Wrong port'
                i+=1
        except:
            print "Failed to connect on",portsList[i][0]
            i+=1
    
    return ser

def close(ser):
    ser.close()

def sendExposure(ser, exp):
    print 'launching sendexp fct'
    ser.write('E') #Send the byte string 'E', wich inform the arduino, the exposure will be sent
    print 'exposure to send : ', exp
    ser.write(str(exp))
    #print 'Exposure set at : ',ser.readline() # Checking that arduino has received the info

def sendLedList(ser, ledRatio):
    print 'launching sendList fct'
    ledSeq = ['r']*ledRatio[0]+['g']*ledRatio[1]+['b']*ledRatio[2]
    ser.write('L') #Send the byte string 'E', wich inform the arduino, the LED list will be sent
    print 'List to send : ', ledSeq
    ser.write(str(len(ledSeq))) #Send the length of the list
    print 'len sent :', ser.readline()
    for char in ledSeq:
        ser.write(char) #send each char of the list to the Arduino
        print 'ASCII char sent : ', ser.readline()
    
##### TESTING SECTION ####
#print 'LAUNCHING TEST'
#ser = connect()
#if ser :
#    ledRatio = [1,3,2]
#    sendLedList(ser,ledRatio)
#    close(ser)
#else :
#    print 'shit happens'