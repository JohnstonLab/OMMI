# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 11:20:42 2019

@author: Louis Vande Perre

Camera initialization function. Initialize a device and load all paramaters
"""
#DEVICE to load - Label, Description, Name
#DEVICE = ['Camera', 'DemoCamera', 'DCam']
DEVICE = ['Zyla','AndorSDK3','Andor sCMOS Camera']

#Acquisition Window (Full Image 128x128 512x512 1392x1040 1920x1080 2048x2048)
AcqWindow= "Full Image"

#PixelReadoutRate (200 MHz - lowest noise  560 MHz - fastest readout)
PixRR="560 MHz - fastest readout"

#Binning (1x1 2x2 4x4 8x8 ) #NOT AVAILABLE IN DEMO
binn=['1x1','2x2','4x4','8x8']
#binn="1" #For demo Cam

#Sensitivity/DynamicRange
#( 12-bit (high well capacity) 12-bit (low noise) 16-bit (low noise & high well capacity))
bit= ['12-bit (high well capacity)','12-bit (low noise)',"16-bit (low noise & high well capacity)"]

#Exposure
exp=10.01

def camInit(mmc):
    """
    Initialize the camera specified in DEVICE list above.
    """

    mmc.loadDevice(*DEVICE)
    mmc.initializeAllDevices()
    mmc.setCameraDevice(DEVICE[0])

    mmc.setProperty(DEVICE[0], 'TriggerMode', 'Internal (Recommended for fast acquisitions)') #Internal (Recommended for fast acquisitions) #External
    mmc.setProperty(DEVICE[0], 'Binning', binn[2])
    mmc.setExposure(DEVICE[0], exp)
    mmc.setProperty(DEVICE[0], 'AcquisitionWindow', AcqWindow) #NOT AVAILABLE IN DEMO
    mmc.setProperty(DEVICE[0], 'PixelReadoutRate', PixRR) #NOT AVAILABLE IN DEMO
    mmc.setProperty(DEVICE[0], 'Sensitivity/DynamicRange', bit[2]) #NOT AVAILABLE IN DEMO
    mmc.setProperty(DEVICE[0],'ElectronicShutteringMode','Global') #Rolling Global #NOT AVAILABLE IN DEMO
    mmc.setProperty(DEVICE[0],'Overlap','Off') #NOT AVAILABLE IN DEMO

    return DEVICE

def defaultCameraSettings(isoiWindow):
    """
    Set the camera settings to default configuration and update the GUI.
    """

    isoiWindow.mmc.clearROI()
    isoiWindow.exposureChange(exp)
    isoiWindow.binChange(binn[2])
    isoiWindow.bitChange(bit[2])
    isoiWindow.shutChange('Global')
    isoiWindow.overlapChange('Off')
