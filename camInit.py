# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 11:20:42 2019

@author: Johnstonlab

Camera initialisation function. Initialise a device and load all parameters
"""

import os

# specify path to micromanager folder and path to µManager config file that has the hardware details of the camera
mmPath = 'C:/Program Files/Micro-Manager-2.0/'
configPath = 'C:/Program Files/Micro-Manager-2.0/zyla.cfg'


# Then set appropriate defaults for your camera, below are for a Andor Zyla 5.5

#Acquisition Window (Full Image 128x128 512x512 1392x1040 1920x1080 2048x2048)
AcqWindow= "Full Image"

#PixelReadoutRate (200 MHz - lowest noise  560 MHz - fastest readout)
PixRR="560 MHz - fastest readout"

#Binning (1x1 2x2 4x4 8x8 )
binn=['1x1','2x2','4x4','8x8']

#Sensitivity/DynamicRange
#( 12-bit (high well capacity) 12-bit (low noise) 16-bit (low noise & high well capacity))
bit= ['12-bit (high well capacity)','12-bit (low noise)',"16-bit (low noise & high well capacity)"]

#Exposure
exp=10.01


# The function below loads your camera using a config file that you created with µManager
# It then applies the defaults defined above to the camera, you can get the correct syntax and available camera options
# for the camera of your choice using the device property browser in µManager. 

def camInit(mmc):
	"""
    Initialize the camera specified by your µManager config file indicated above.
    Load and initialise this camera and set default properties for the camera as detailed above.
    """
    
	cwd = os.getcwd()
	os.chdir(mmPath)
	mmc.loadSystemConfiguration(configPath)
	mmc.initializeAllDevices()
	DEVICE = mmc.getLoadedDevices()
	mmc.setCameraDevice(DEVICE[0])
	os.chdir(cwd)
	mmc.setProperty(DEVICE[0], 'TriggerMode', 'Internal (Recommended for fast acquisitions)')
	mmc.setProperty(DEVICE[0], 'Binning', binn[2])
	mmc.setExposure(DEVICE[0], exp)
	mmc.setProperty(DEVICE[0], 'AcquisitionWindow', AcqWindow)
	mmc.setProperty(DEVICE[0], 'PixelReadoutRate', PixRR)
	mmc.setProperty(DEVICE[0], 'Sensitivity/DynamicRange', bit[2])
	mmc.setProperty(DEVICE[0],'ElectronicShutteringMode','Global') #Rolling Global
	mmc.setProperty(DEVICE[0],'Overlap','Off')
	return DEVICE

def defaultCameraSettings(OMMIwindow):
    """
    Set the camera settings to default configuration and update the GUI.
    """

    OMMIwindow.mmc.clearROI()
    OMMIwindow.exposureChange(exp)
    OMMIwindow.binChange(binn[2])
    OMMIwindow.bitChange(bit[2])
    OMMIwindow.shutChange('Global')
    OMMIwindow.overlapChange('Off')
