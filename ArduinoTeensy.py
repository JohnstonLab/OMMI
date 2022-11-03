# -*- coding: utf-8 -*-
"""
Created on Tue Sep 03 11:54:21 2019

@author: Louis Vande Perre

Script containing the ArduinoTeensy class code.

"""

import serial
import time
import serial.tools.list_ports as lsports
import struct

from PyQt5.QtCore import QObject, pyqtSignal


class Arduino(QObject):
    """
    Class of Arduino Teensy.
    Inspired from : https://github.com/mick001/Arduino-Comm-Class/blob/master/ArduinoUnoClass.py
    """

    syncStarted = pyqtSignal()
    syncFinished = pyqtSignal()
    #Color mode in R-B acquisition
    rbColorModes = ['Red and Blue', 'Red only', 'Blue only']

    def __init__(self, led,speed=9600, timeout=1, parent=None):
        """ CLASS CONSTRUCTOR """

        QObject.__init__(self,parent)

        self.led = led
        self.speed = speed
        self.timeout = timeout

        self.connected = False
        self.ser = None
        self.port = None

        attempt = 0
        while (not self.connected) and attempt<20:
            self._portScanning()
            time.sleep(0.5)
            attempt+=1

    def _portScanning(self):
        """
        Check all the computer's ports and try to connect to Teensy devices.
        """
        #The function (comports())returns an iterable that yields tuples of three strings:
            ## port name as it can be passed to serial.Serial or serial.serial_for_url()
            ## description in human readable form
            ## sort of hardware ID. E.g. may contain VID:PID of USB-serial adapters.
        portsList = lsports.comports()
        #Scan each ports to find the Teensy board (Cyclops' Arduino) and connect to it
        for i in range(0,len(portsList)):
            try:
                print("Trying...",portsList[i][0])
                if ('USB Serial Device' in portsList[i][1]) and (not self.connected):  ## change from 'Teensy' to 'USB Serial Device'
                    self.ser = serial.Serial(portsList[i][0], self.speed, timeout=self.timeout)
                    self.port=portsList[i][0]
                    self._ledHandshake()
                else:
                    print('Wrong port')
                    i+=1
            except:
                print("Failed to connect on",portsList[i][0])
                i+=1


    def _ledHandshake(self):
        """
        Check which LED is controlled by this Teensy.
        """

        self.sendChar('C') #Send C char for Connection.
        ledDriver = self.readData(1,printData=True,integers = True) #nlines,printData=False,array=True,integers=False,Floaters=False
        if ledDriver[0] == self.led:
            self.connected = True
            print('Arduino connected')
        else:
            self.ser.close()
            self.ser=None

    def __repr__(self):
        """
        How the object is representing itself when printed/called
        """

        return "Arduino object:\n\nArduino connected to: %s\nspeed: %s\n" %(self.port,self.speed)

    def blinkingLED(self,delay):
        """
        Turn on the LED at certain time interval.
        """
        for i in range(10):
            time.sleep(delay)
            self.sendChar('H')   # send the byte string 'H'
            time.sleep(delay)   # wait delay seconds
            self.sendChar('L')   # send the byte string 'L'

    def sendChar(self,char):

        """ SEND A CHARACTER (CHAR) TO ARDUINO through serial port"""

        if len(str(char))>1 or char == "":
            raise ValueError('Only a single character is allowed')

        # Optional print
        # print(bytes(str(char).encode()))

        valueToWrite = bytes(str(char).encode())

        try:
            send = self.ser.write(valueToWrite)
#            print(
#            """
#            Data sent succesfully.
#            Data sent: %s
#            Immediate response: %s
#            """
#            %(char,send))
        except Exception as e:
            print(("Some error occurred, here is the exception: ",e))


    def sendInteger(self, integer,printR=False):

        """
            SEND AN INTEGER (INT) TO ARDUINO through serial port
            Optionally a report is printed if printR = True
            Note that integers are converted into raw binary code readable
            from Arduino through the module struct.

            Special thanks to Ignacio Vazquez-Abrams for the suggestion on
            StackOverflow.
        """

        try:
            integer = int(integer)
        except Exception as e:
            print(e)
        try:
            dataToSend = struct.pack('>B',integer)
            self.ser.write(dataToSend)
            if printR:
                print(("Sent the integer %s succesfully" %integer))
        except Exception as e:
            print(("Some error occurred, here is the exception: ",e))

    def sendFloat(self, floatNb, printR = False):
        """
        Send a float to arduino through serial port.
        Optionally a report is printed if printR = True.
        """
        try:
            floatNb = float(floatNb)
        except Exception as e:
            print(e)
        try:
            dataToSend = str(floatNb)
            for char in dataToSend :
                self.sendChar(char)
            if printR:
                print(("Sent the floatNb %s succesfully" %floatNb))
        except Exception as e:
            print(("Some error occurred, here is the exception: ",e))


    def sendIntArray(self,array,delay=2,printR=False):

        """
            SEND AN ARRAY OF INTEGERS (INT) TO ARDUINO through serial port
            Optionally a report is printed if printR = True

            Note that the array is sent as a sequence of integers
        """

        try:
            for i in array:
                self.sendInteger(i)
                time.sleep(delay)
                if printR:
                    print(("Sent integer %s" %i))
            if printR:
                print(("Sent the array %s succesfully" %array))
        except Exception as e:
            print(("Some error occurred, here is the exception: ",e))


    def sendIllumTime(self, illumTime):
        """
        Send the time within a LED ON from the beggining of an acquisition.
        """
        sync = True
        self.sendChar('E')
        msIllumTime = int(illumTime)
        usIllumTime = int(round((illumTime-msIllumTime),3)*1000) #Round and convert to us then to INT
        #Sending ms component
        for char in str(msIllumTime):
            self.sendChar(char)
#        time.sleep(0.8) # time for parse INT
        intSent = self.readData(1, integers = True)
        print(intSent,msIllumTime)
        nbSent = intSent[0]
        if nbSent != msIllumTime:
            sync = False
        #Sending us component
        for char in str(usIllumTime):
            self.sendChar(char)
#        time.sleep(0.8)
        intSent = self.readData(1, integers = True)
        print(intSent,usIllumTime)
        nbSent = intSent[0]
        if nbSent != usIllumTime:
            sync = False
        return sync

    def rbModeSettings(self, greenFrameInterval, colorMode):
        """
        Change the LED alternation mode to rbMode and send the interval between
        green frames to the LED driver.
        Note that there are 3 submodes in the rbMode : Blue and red, red only
        and blue only.
        """
        sync = True
        #Send M char to inform arduino the mode will be set
        self.sendChar('M')
        #Send G char to chose the rbMode
        if colorMode == Arduino.rbColorModes[0] :
            self.sendChar('G')
            #Send the greenFrameInterval variable
            for char in str(greenFrameInterval):
                self.sendChar(char)
        elif colorMode == Arduino.rbColorModes[1]:
            self.sendChar('R')
            #Send the greenFrameInterval variable
            for char in str(greenFrameInterval):
                self.sendChar(char)
        elif colorMode == Arduino.rbColorModes[2]:
            self.sendChar('B')
            #Send the greenFrameInterval variable
            for char in str(greenFrameInterval):
                self.sendChar(char)
#        time.sleep(0.8) #Wait that ParseInt() fct of the arduino timed out
        #Verification of the value sent
        intSent = self.readData(1, integers = True)
        nbSent = intSent[0]
        if nbSent != greenFrameInterval:
            sync = False
        return sync

    def rgbModeSettings(self, ledRatio):
        """
        Change the LED alternation mode to rgbMode and send the LED alternation
        sequence to the LED driver.
        """
        sync = True
        ledSeq = [0]*ledRatio[0]+[1]*ledRatio[1]+[2]*ledRatio[2]
        print(ledSeq)
        #Send M char to inform arduino the mode will be set
        self.sendChar('M')
        #Send L char to chose the rgbMode and send the List
        self.sendChar('L')

        #Send the LED alternation sequence
        for char in str(int(len(ledSeq))):
            self.sendChar(char)
        time.sleep(0.05) #Wait that ParseInt() fct of the arduino timed out
        #Verification of the value sent
        intSent = self.readData(1, integers = True)
        print(intSent)
        nbSent = intSent[0]
        if nbSent != len(ledSeq):
            sync = False
        for ledInt in ledSeq:
            self.sendChar(str(ledInt))
            intSent = self.readData(1, integers = True)
            print(intSent)
            nbSent = intSent[0]
            if nbSent != ledInt:
                sync = False
        return sync

    ### Quick communication protocol ###
    def resetFrameCounter(self):
        """
        Send Z char to tell reset the framecounter of the arduino to Zero.
        Can be used to speedup the process between loop acquisition.
        """
        self.sendChar('Z')

    def oneColor(self, color, illumTimeList):
        """
        Put the cyclops driver in one color mode with the right time of illum
        for the conceirned LED.
        """
        sync = False
        failCount = 0
        while(not sync and failCount > 10):
            sync = self.sendIllumTime(illumTimeList[self.led])
            print('IllumTime sent : ', illumTimeList[self.led])
            print('sync value of attempt to set illumtime  : ', sync)
            if not sync:
                failCount+=1
                time.sleep(0.1*failCount)
        #Window to prevent user that synchronization uncomplete
        if color == 0:
            self.sendChar('R')
        elif color == 1:
            self.sendChar('G')
        elif color == 2:
            self.sendChar('B')

    def ledOff(self):
        """
        Disconnect the current trigger mode of the LED driver,
        it will no more turn his LED on
        """
        self.sendChar('N')

    def readData(self,nlines,printData=False,array=True,integers=False,Floaters=False):

        """
            READ DATA FROM ARDUINO through serial port.

            The function reads the first nlines and returns an array of
            strings by default.
            If printData is true it prints the data to the console.
            If array is True it returns an array.
            If integers or Floaters are either True, it returns an array of
            either integers or float.

            Use the Serial.print() function on Arduino to send data
            Serial port on Arduino should be initialized at 9600 baud.
            Example:
                    void setup()
                    {
                        Serial.begin(9600);
                    }

                    void loop()
                    {
                        // Sending integer 1 each second
                        Serial.print(1);
                        delay(1000);
                    }

            Carefully note that the function will loop until it collects
            exactly nlines readings or exceptions.
        """

        data = []

        i = 0

        while i < nlines:

            try:
                print('trying to read')
                value = self.ser.readline()
                #print 'read value : ', value
                data.append(value)
                i += 1
            except Exception as e:
                print(e)
                i += 1

        if printData:
            for k in data:
                print(k)

        if array and not integers and not Floaters:
            return data
        elif array and integers and not Floaters:
            dataToReturn = []
            for j in data:
                try:
                    dataToReturn.append(int(j))
                except:
                    dataToReturn.append("None")
            return dataToReturn
        elif array and not integers and Floaters:
            dataToReturn = []
            for j in data:
                try:
                    dataToReturn.append(float(j))
                except:
                    dataToReturn.append("None")
            return dataToReturn
        else:
            print("Nothing to return since array = False")


    def synchronization(self, illumTime, rgbLedRatio=None, greenFrameInterval=None, colorMode=None):
        """
        Function in charge of the
        """
        self.syncStarted.emit()
        if self.isConnected():
            print(('Driver num ',self.led,' is connected'))
            sync = False
            while(not sync):
                sync = self.sendIllumTime(illumTime[self.led])
                print('sync value of attempt to set illumtime  : ', sync)
            if rgbLedRatio: #if rgbLedRatio is not None, this statement will be executed
                sync = False
                while(not sync):
                    sync = self.rgbModeSettings(rgbLedRatio)
                    print('sync value of attempt to set rgbmode : ', sync)
            elif greenFrameInterval and colorMode:
                self.rbModeSettings(greenFrameInterval,colorMode)#TO DO : add the checking of color mode here
            self.closeConn()
        self.syncFinished.emit()

    def isConnected(self):
        """
        This function return True if the serial communication is open, False if not
        """
        return self.connected

    def closeConn(self):
        """
        CLOSE THE USB CONNECTION
        """

        self.ser.close()
        self.connected = False
        print(("Arduino connection to "+str(self.port)+" closed!"))


### Arduino-related function


def synchronization(illumTime, rgbLedRatio=None, greenFrameInterval=None, colorMode=None):
    """
    Initialize and send the information to each LED driver.
    """
    print('Synchronization fct from Teensy called')
    ledDriverNb=[0,1,2] #[Red, Green, Blue]
    for driverNb in ledDriverNb:
        driver = Arduino(driverNb)
        if driver.isConnected():
            print(('Driver num ',driverNb,' is connected'))
            sync = False
            while(not sync):
                sync = driver.sendIllumTime(illumTime[driverNb])
                print('sync value of attempt to set illumtime  : ', sync)
            if rgbLedRatio: #if rgbLedRatio is not None, this statement will be executed
                sync = False
                while(not sync):
                    sync = driver.rgbModeSettings(rgbLedRatio)
                    print('sync value of attempt to set rgbmode : ', sync)
            elif greenFrameInterval and colorMode:
                driver.rbModeSettings(greenFrameInterval,colorMode)#TO DO : add the checking of color mode here
            driver.closeConn()
        else:
            print(('Driver num ',driverNb,' is NOT connected'))



###TEST SECTION :

if __name__ == '__main__':

    print('test')
    #blueArduino = Arduino(2)
#    if blueArduino:
#        blueArduino.blinkingLED(0.5)
#    print blueArduino
    illumTimeList = [10.07,10.07,5]
    greenFrameInterval = 5
    colorMode = 'Blue only'
    synchronization(illumTimeList, greenFrameInterval = greenFrameInterval, colorMode = colorMode)
    #blueArduino.synchronization(illumTime,greenFrameInterval = greenFrameInterval,colorMode = colorMode)
    #blueArduino.oneColor(2,illumTimeList)
#    redArduino = Arduino(0)
#    exposure = 10.07
#    sync = redArduino.sendIllumTime(exposure)
#    print sync
#    greenFrameInterval = 20
#    sync = redArduino.rbModeSettings(greenFrameInterval, )
#    print sync
##    try:
##        blueArduino.closeConn()
##    except:
##        print 'no way to close blueArduino'
#    try:
#        redArduino.closeConn()
#    except:
#        print 'no way to close redArduino'
    print('endTest')
