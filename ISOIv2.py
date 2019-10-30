# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 10:51:18 2019

@author: Louis Vande Perre

Main file of ISOI software.
v2 - using thread to launch an acquisition.

"""

#Packages import
import sys
import MMCorePy
import cv2
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QAbstractItemView
from time import time, sleep
import os
from os import path
import ctypes
import shutil



#Class import
from SequenceAcquisition import SequenceAcquisition
from SignalInterrupt import SignalInterrupt 
from ArduinoTeensy import Arduino
from OdourMap import OdourMap

#Function import
from histogram import histoInit, histoCalc
from crop import crop_w_mouse
from camInit import camInit, defaultCameraSettings
from saveFcts import fileSizeCalculation, jsonFileLoading
from Labjack import labjackInit, greenOn, greenOff, redOn, redOff, blueOn, blueOff
from ParsingFiles import load2DArrayFromTxt, get_immediate_subdirectories, getTifLists, splitColorChannel, getTxtList
#from ArduinoComm import connect, sendExposure, sendLedList, close




class isoiWindow(QtWidgets.QMainWindow):
    ### Class attributes - needed for displays information ###
    
    #trackbar
    div=100
    step=1/float(div)
    
    #Exposure (just here to keep it as global var)
    #expMin=0.0277
    expMin=5.0
    expMax=99.0
    
    #LEDs Ratio
    ledFrameNbMax=10
    ledFrameNbMin=0
    
    #File Size params
    framePerFileDefault =512
    
    #LED lit time (as a ratio of the exposure time) 
    ratioMin = 0.05
    ratioMax = 3.
    ratioDefault = 0.5
    ratioStep = 0.05
    
    #PyQt Signals definition, allows communication between different devices
    updateFramesPerFile = pyqtSignal() ##Better to use pyqtSlot ?
    settingsLoaded = pyqtSignal()
    
    #Bit depth (cam properties)
    bit= ['12-bit (high well capacity)','12-bit (low noise)',"16-bit (low noise & high well capacity)"]
    
    #Binning (cam properties)
    binn=['1x1','2x2','4x4','8x8']
    
    #Color mode in R-B acquisition
    rbColorModes = ['Red and Blue', 'Red only', 'Blue only']
    
    #LED trigger modes 
    ledTriggerModes = ['Labjack', 'Cyclops']
    
    def __init__(self, mmc, DEVICE, labjack,parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('isoi_window_V2.ui', self)
        
        ### Instance attributes ##
        self.mmc = mmc
        self.DEVICE = DEVICE
        self.labjack = labjack
        
        # Connect push buttons
        self.cropBtn.clicked.connect(self.crop)
        self.histoBtn.clicked.connect(self.oldHisto)
        self.runSaveBtn.clicked.connect(self.runCheck)
        self.runSaveBtn.setEnabled(False)
        self.abortBtn.setEnabled(False)
        self.arduinoBtn.setEnabled(False)
        self.arduinoBtn.clicked.connect(self.arduinoSync)
        self.loopBtn.setEnabled(False)
        self.loopBtn.clicked.connect(self.loopCheck)
        self.loadBtn.clicked.connect(self.loadZyla)
        self.unloadBtn.clicked.connect(self.unloadDevices)
        self.approxFramerateBtn.clicked.connect(self.approxFramerate)
        self.testFramerateBtn.clicked.connect(self.testFramerateInt)
        self.loadSettingsFileBtn.clicked.connect(self.loadjsonFile)
        self.defaultSettingsBtn.clicked.connect(self.defaultSettings)
        self.savingPathBtn.clicked.connect(self.browseSavingFolder)
        
        self.loadFileBtn.clicked.connect(self.loadFolder)
        self.splitBtn.clicked.connect(self.processRunExperiment)
        self.splitAllBtn.clicked.connect(self.processAllRunExperiments)
        
        self.loadExpFileBtn.clicked.connect(self.loadLoopExp)
        self.loadStimSeqBtn.clicked.connect(self.loadStimSequence)
        self.splitStimFileBtn.clicked.connect(self.splitStimFiles)
        self.splitFilesOdourBtn.clicked.connect(self.splitLoopExp)
        
        self.loadOdourFolderBtn.clicked.connect(self.loadExpOdFolder)
        self.mapBtn.clicked.connect(self.createOdourMap)
        
        #Connect Signals
        self.updateFramesPerFile.connect(self.fileSizeSetting)
        
        ###### ComboBoxes ######
        
        #Binning selection
        self.binBox.addItem(isoiWindow.binn[0])
        self.binBox.addItem(isoiWindow.binn[1])
        self.binBox.addItem(isoiWindow.binn[2])
        self.binBox.addItem(isoiWindow.binn[3])
        self.binBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Binning'))
        self.binBox.currentTextChanged.connect(self.binChange)
        
        #Bit depth selection
        self.bitBox.addItem(isoiWindow.bit[0])
        self.bitBox.addItem(isoiWindow.bit[1])
        self.bitBox.addItem(isoiWindow.bit[2])
        self.bitBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Sensitivity/DynamicRange'))
        self.bitBox.currentTextChanged.connect(self.bitChange)
        
        #Shutter mode selection
        self.shutBox.addItem("Rolling")
        self.shutBox.addItem("Global")
        self.shutBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'ElectronicShutteringMode'))
        self.shutBox.currentTextChanged.connect(self.shutChange)
        
        
        #Overlap Mode
        self.overlapBox.addItem('On')
        self.overlapBox.addItem('Off')
        self.overlapBox.setCurrentText(self.mmc.getProperty(self.DEVICE[0], 'Overlap'))
        self.overlapBox.currentTextChanged.connect(self.overlapChange)

        
        #LEDs trigger mode selection
#        self.ledTrigBox.addItem(isoiWindow.ledTriggerModes[1])
#        self.ledTrigBox.addItem(isoiWindow.ledTriggerModes[0])
#        self.ledTrigBox.setCurrentText(isoiWindow.ledTriggerModes[0])
#        self.ledTrigBox.currentTextChanged.connect(self.ledTrigChange)
        
        #Color mode of rb alternance box
        self.rbColorBox.addItem(isoiWindow.rbColorModes[0])
        self.rbColorBox.addItem(isoiWindow.rbColorModes[1])
        self.rbColorBox.addItem(isoiWindow.rbColorModes[2])
        self.rbColorBox.setCurrentText(isoiWindow.rbColorModes[0])
        
        ####### Slider #####
        self.expSlider.setMinimum(isoiWindow.expMin)
        self.expSlider.setMaximum(isoiWindow.expMax)
        self.expSlider.setValue(self.mmc.getExposure())  
        self.expSlider.valueChanged.connect(self.exposureChange)
        self.expSlider.setSingleStep(isoiWindow.step*10) ##doesn't affect anything 
        
        #### Spinboxes ###
        
        #EXPOSURE
        self.C_expSb.setMaximum(isoiWindow.expMax)
        self.C_expSb.setMinimum(isoiWindow.expMin)
        self.C_expSb.setValue(self.mmc.getExposure())
        self.C_expSb.valueChanged.connect(self.exposureChange)
        self.C_expSb.setSingleStep(isoiWindow.step)
        
        #Experiment duration
        self.experimentDuration.setSingleStep(float(isoiWindow.step))
        self.experimentDuration.setMaximum(1000)
        
        #LEDs ratios
        self.gRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.rRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.bRatio.setMinimum(isoiWindow.ledFrameNbMin)
        self.gRatio.setMaximum(isoiWindow.ledFrameNbMax)
        self.rRatio.setMaximum(isoiWindow.ledFrameNbMax)
        self.bRatio.setMaximum(isoiWindow.ledFrameNbMax)
        
        #File size
        self.framePerFileBox.setValue(isoiWindow.framePerFileDefault)
        self.framePerFileBox.valueChanged.connect(self.updateFramesPerFile.emit)
      
        #Inteval red LED on
        self.rExpRatio.setValue(isoiWindow.ratioDefault)
        self.rExpRatio.setMaximum(isoiWindow.ratioMax)
        self.rExpRatio.setSingleStep(isoiWindow.ratioStep)
        self.rExpRatio.setMinimum(isoiWindow.ratioMin)
        
        #Inteval green LED on
        self.gExpRatio.setValue(isoiWindow.ratioDefault)
        self.gExpRatio.setMaximum(isoiWindow.ratioMax)
        self.gExpRatio.setSingleStep(isoiWindow.ratioStep)
        self.gExpRatio.setMinimum(isoiWindow.ratioMin)
        
        #Inteval blue LED on
        self.bExpRatio.setValue(2*isoiWindow.ratioDefault)
        self.bExpRatio.setMaximum(isoiWindow.ratioMax)
        self.bExpRatio.setSingleStep(isoiWindow.ratioStep)
        self.bExpRatio.setMinimum(isoiWindow.ratioMin)
        
        #####
        
        #Name text area
        self.experimentName.insert("DefaultName")
        
        #Initialize frames per files text label
        self.fileSizeSetting()
        
        #Initialize exposure label
        self.realExp.setText(str(self.mmc.getExposure()))
        
        #Initialize framerate label
        self.cycleTime = self.approxFramerate()
        
        #ProgressBar
        self.progressBar.setMinimum(0)
        self.progressBar.setValue(0)
        
        #LEDs toggle buttons
        self.Green.stateChanged.connect(self.green)
        self.Red.stateChanged.connect(self.red)
        self.Blue.stateChanged.connect(self.blue)
        
        #Led sequence mode toogle buttons
        self.rgbMode.stateChanged.connect(self.ledSequenceModeCheck)
        self.rbMode.stateChanged.connect(self.ledSequenceModeCheck)
        
        #Allow the user to selected multiple items in the QlistWidget
        self.odourFoldersList.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    
    #################################
    #### Camera settings methods ####
    #################################
    
    ###Button related###
    #Organized like the GUI panel
    
    def exposureChange(self, expVal):
        """
        Change the exposure in the camera settings and update the GUI 
        with the real exposure.
        """
        #exp=expVal/float(div)
        self.C_expSb.setValue(expVal) #update spinbox value
        self.expSlider.setValue(expVal) #update slider value
        print 'exposure wanted : ', expVal
        try:
            self.mmc.setExposure(DEVICE[0], expVal)
            self.realExp.setText(str(self.mmc.getExposure()))
        except:
            print "CMM err, no possibility to set exposure"
    
    def approxFramerate(self):
        """
        This function approximate the framerate. Approximation based on Zyla
        specifications mentioned in the hardware user guide.
        """
        print('Approximation of the framerate')
        ##### From Hardware User Guide #####
        ### settings > Global Shutter and external/software triggering,
        ### Sensor Readout Rate = 560MHz 
        row =  9.24E-6      #(s)
        fullFrame= 9.98E-3  #(s)
        interFrame= 9*row
        startDelay= 2*row
        #Overlap Off :
            #CycleTime = exposure + 1 Frame + 1 interframe + 5 rows
        #Overlap On :
            #CycleTime =  exposure dependant (look at documentation)
        
        if self.binBox.currentText() == '4x4':
            fullFrameNbPix = 640*540 #Binning4x4
        elif self.binBox.currentText() == '1x1':
            fullFrameNbPix = 2560*2160 #Binning1x1
        elif self.binBox.currentText() == '2x2':
            fullFrameNbPix = 1280*1080 #Binning2x2
        elif self.binBox.currentText() == '8x8':
            fullFrameNbPix = 320*270 #Binning1x1
            
        exposure = float(self.realExp.text())*1E-3 #conversion in s
        print('exposure : ',exposure)
        ROI = self.mmc.getROI()
        print('ROI : ',ROI)
        nbPix = ROI[-1]*ROI[-2] #(horizontal nb of pix) * (vertical nb of pix), last objects of ROI list
        
        print('nbPix : ',nbPix)
        frameRatio = float(nbPix)/fullFrameNbPix #One must be float to have a float div
        print('frameRatio : ',frameRatio)
        
        #Cycle time calculation
        #Note that it doesn't take the LED triggering by the labjack in count
        cycleTime = exposure + fullFrame*frameRatio+interFrame+5*row+startDelay+3E-3 #seconds #add 3ms to secure the approximation
        print('cycleTime : ',cycleTime)
        self.approxFramerateLabel.setText(str(round(1/cycleTime,2)))
        return cycleTime
    
    def testFramerateInt(self):
        """
        This function test the framerate. Fire a serie of 5 images using the 
        internal trigger mode and mesure the average cycle time.
        """
        cycleTime = 0
#        previousTriggerMode = self.mmc.getProperty(self.DEVICE[0], 'TriggerMode')
#        triggerMode = 'External'
#        print('test of the framerate')
#        self.triggerChange(triggerMode)
#        if self.triggerModeCheck(triggerMode):
        self.mmc.startContinuousSequenceAcquisition(1)
        imageCount = 0
        imageNb = 5
        first=True
        while (imageCount< imageNb):
            if (self.mmc.getRemainingImageCount() > 0):
                self.mmc.clearCircularBuffer() ## remove the last image from the circular buffer
                if first:
                    start = time()
                    first = not(first)
                else:
                    end = time()
                    cycleTime+= (end-start)/(imageNb-1) #5 images give you 4 interval
                    start = time()
                imageCount+=1
        self.mmc.stopSequenceAcquisition()
        self.testFramerateLabel.setText(str(round(1/cycleTime,2)))
        return cycleTime
    
    
    def binChange(self, binn):
        """
        Change the Binning in the camera settings and update the GUI.
        """
        try:
            self.mmc.setProperty(self.DEVICE[0], 'Binning', str(binn))
            realBinning = self.mmc.getProperty(self.DEVICE[0],'Binning')
            self.binBox.setCurrentText(realBinning) #Ensure that the change are effective
                                                    #and update the GUI
        except:
            print 'CMM err, no possibility to set Binning'

    def bitChange(self, bit):
        """
        Change the Sensitivity/DynamicRange in the camera settings and update the GUI.
        """
        try:
            self.mmc.setProperty(self.DEVICE[0], 'Sensitivity/DynamicRange', str(bit))
            actualBitDepth = self.mmc.getProperty(self.DEVICE[0],'Sensitivity/DynamicRange')
            self.bitBox.setCurrentText(actualBitDepth)
        except:
            print 'CMM err, no possibility to set Sensitivity/DynamicRange'
            
    def shutChange(self,shutterMode):
        """
        Change the ElectronicShutteringMode in the camera settings and update the GUI.
        """
        try:
            self.mmc.setProperty(self.DEVICE[0],'ElectronicShutteringMode',str(shutterMode))
            actualShutterMode = self.mmc.getProperty(self.DEVICE[0], 'ElectronicShutteringMode')
            self.shutBox.setCurrentText(actualShutterMode)
        except:
            print 'CMM err, no possibility to set ElectronicShutteringMode'
        
    def triggerChange(self, triggerMode):
        """
        Change the TriggerMode in the camera settings and update the GUI.
        """
        try:
            self.mmc.setProperty(self.DEVICE[0],'TriggerMode',str(triggerMode))
            actualTriggerMode = self.mmc.getProperty(self.DEVICE[0], 'TriggerMode')
            #self.triggerBox.setCurrentText(actualTriggerMode)
            print 'Trigger mode set at : ',actualTriggerMode
        except:
            print 'CMM err, no possibility to set TriggerMode'

    def overlapChange(self, overlap):
        """
        Change the TriggerMode in the camera settings and update the GUI.
        """
        try:
            self.mmc.setProperty(self.DEVICE[0],'Overlap', str(overlap))
            actualOverlap = self.mmc.getProperty(self.DEVICE[0], 'Overlap')
            self.overlapBox.setCurrentText(actualOverlap)
        except:
            print "CMM err, no possibility to set Overlap mode"
            
    def loadZyla(self):
        """
        Load a device on the MMC API.
        The device loaded will be used to acquire images.
        """
        try:
            self.DEVICE = camInit(self.mmc)
            print 'Device ',self.DEVICE[0],' loaded'
        except:
            print 'CMM error : fail to load device'
    
    def unloadDevices(self):
        """
        Unload all devices from the MMC API > closing communication.
        """
        try:
            self.mmc.unloadAllDevices()
            print 'all devices UNLOADED'
        except:
            print 'CMM error : fail to unload all devices'
    
    
    ###LED ligtening###
    def green(self,toggle_g):
        """
        Turn on or off the green LED in function of the QCheckBox state.
        """
        if toggle_g:
            greenOn(self.labjack)
        else :
            greenOff(self.labjack)
          
    def red(self,toggle_r):
        """
        Turn on or off the red LED in function of the QCheckBox state.
        """
        if toggle_r:
            redOn(self.labjack)
        else :
            redOff(self.labjack)    
            
    def blue(self,toggle_b):
        """
        Turn on or off the blue LED in function of the QCheckBox state.
        """
        if toggle_b:
            blueOn(self.labjack)
        else :
            blueOff(self.labjack)
    
    ### CROP CAMERA IMAGE ###
    def crop(self):
        """
        Set the ROI of the camera.
        If a ROI is mouse drawn on the screen > this ROI is selected.
        Else the ROI is reset() to the default one. 
        """
        choice = QMessageBox.question(self, 'ROI reset',
                                            "This action will reset the ROI, do you want to continue ?",
                                            QMessageBox.Yes | QMessageBox.No)
        if choice == QMessageBox.Yes:
            triggerMode = 'Internal (Recommended for fast acquisitions)'
            if self.triggerModeCheck(triggerMode):
                greenOn(self.labjack)
                sleep(0.5)
                self.mmc.clearROI()
                self.mmc.snapImage()
                img = self.mmc.getImage()
                (x,y,w,h) = crop_w_mouse(img,self.mmc.getROI())
                self.mmc.setROI(x,y,w,h)
                print "image width: "+str(self.mmc.getImageWidth())
                print "image height: "+str(self.mmc.getImageHeight())
                cv2.destroyAllWindows()
                greenOff(self.labjack)
                self.updateFramesPerFile.emit()
        else:
            print('Cropping aborted')
    
    ### LOADING EXPERIMENT SETTINGS ###    
    
    def defaultSettings(self):
        """
        Reset the camera and acquisition settings.
        """
        print 'default settings loading'
        
        # Reset Camera Settings 
        defaultCameraSettings(self)
        # Reset Acquisition Settings #TO DO ?

    
    def loadjsonFile(self):
        """
        Use QFileDialog to display a window and ask for a file to load with
        a filter on .json file.
        """
            
        selectedFile = QFileDialog.getOpenFileName(self, 'Open configuration file', filter=('JSON configuration file (*.json)'))
        #FileName contains the file name and the filter so we select only first component
        fileName=selectedFile[0]
        if path.isfile(fileName):
            self.loadSettings(fileName)
        else:
            print('No file selected')
        
    
    def loadSettings(self, settingsPath):
        """
        Load the CFG file, update all the experiment settings with infos from the file.
        """
        print 'Loading : ',settingsPath
        #POP UP window to avoid none path calling
        cfgDict = jsonFileLoading(settingsPath)
        
        ### Load camera settings ###
        try:
            camSettingsDict = cfgDict['Camera settings']
            ROI = camSettingsDict["ROI"]
            self.mmc.setROI(ROI[0],ROI[1],ROI[2],ROI[3])
            self.exposureChange(camSettingsDict["Exposure"])
            self.binChange(camSettingsDict["Binning"])
            self.bitChange(camSettingsDict["Bit depth"])
            self.shutChange(camSettingsDict["Shutter mode"])
            self.triggerChange(camSettingsDict["Trigger mode"])
            self.overlapChange(camSettingsDict["Overlap mode"])
        except:
            print 'Camera settings dictionary is not accessible'
            
        ### Load acquisiton settings
        try:
            acqSettings = cfgDict["Acquisition settings"]
            try:
                expRatio = acqSettings['LED illumination time (% of exposure)']
                self.rExpRatio.setValue(expRatio[0])
                self.gExpRatio.setValue(expRatio[1])
                self.bExpRatio.setValue(expRatio[2])
            except:
                print 'old value mode for the LED illum time'
                self.rExpRatio.setValue(acqSettings['LED illumination time (% of exposure)'])
                self.gExpRatio.setValue(acqSettings['LED illumination time (% of exposure)'])
                self.bExpRatio.setValue(acqSettings['LED illumination time (% of exposure)'])
            #self.ledTrigBox.setCurrentText(acqSettings['LED trigger mode'])
            ledSequenceMode = acqSettings['LED switching mode']
            if ledSequenceMode == "rgbMode":
                self.rgbMode.setChecked(True)
                self.rbMode.setChecked(False)
                self.rRatio.setValue(acqSettings["(RGB) LED ratio"][0])
                self.gRatio.setValue(acqSettings["(RGB) LED ratio"][1])
                self.bRatio.setValue(acqSettings["(RGB) LED ratio"][2])
            elif ledSequenceMode == "rbMode":
                self.rgbMode.setChecked(False)
                self.rbMode.setChecked(True)
                self.gInterval.setValue(acqSettings["(RB) Green frames interval"])
                self.rbColorBox.setCurrentText(acqSettings["(RB) Color(s)"])
        except:
            print 'Acquisition settings dictionary is not accessible'
        try:
            self.experimentDuration.setValue(cfgDict['Global informations']['Duration'])
        except:
            print 'Duration not accessible in this CFG file'
            
        self.settingsLoaded.emit()
    
    ### Msg display ###
    def triggerModeCheck(self, triggerMode):
        """
        Check if the camera trigger mode is set to the triggerMode argument.
        Pop-up window is generated if the wrong trigger mode is set on.
        """
        print triggerMode
        if self.mmc.getProperty(self.DEVICE[0], 'TriggerMode') != triggerMode:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Set the trigger mode to : \n" + triggerMode)
            msg.setWindowTitle("Trigger mode warning")
            msg.exec_()
            return False
        else:
            return True
        
    
    ######################################
    #### Acquisition settings methods ####
    ######################################
    
    def ledTrigChange(self):
        """
        Handle a change in the LED trigger mode.
        """
        #Only Labjack mode for the moment so not implemented for the moment.
        print 'm'
    
    def ledSequenceModeCheck(self):
        """
        Check wich LED sequence mode is selected and enable the good buttons.
        Return the mode selected
        """
        mode = None
        if self.rgbMode.isChecked() and self.rbMode.isChecked() :
            self.runSaveBtn.setEnabled(False)
            self.arduinoBtn.setEnabled(False)
            self.loopBtn.setEnabled(False)
        elif self.rgbMode.isChecked():
            self.runSaveBtn.setEnabled(True)
            self.arduinoBtn.setEnabled(True)
            self.loopBtn.setEnabled(True)
            mode ="rgbMode"
        elif self.rbMode.isChecked():
            self.runSaveBtn.setEnabled(True)
            self.arduinoBtn.setEnabled(True)
            self.loopBtn.setEnabled(True)
            mode ="rbMode"
        else:
            self.runSaveBtn.setEnabled(False)
            self.arduinoBtn.setEnabled(False)
            self.loopBtn.setEnabled(False)
        return mode
    
    def fileSizeSetting(self):
        """
        Calculate the size of each .tif file in function of the number of frames
        per file wanted.
        """
        framePerFile = self.framePerFileBox.value()
        #sizeMax = self.fileSize.value()
        ROI = self.mmc.getROI()
        bitDepth = self.bitBox.currentText()
        if bitDepth == isoiWindow.bit[2]:
            bitPPix = 16 #Nb of bits per pixel
        else:
            bitPPix = 12
        
        sizeMax = fileSizeCalculation(framePerFile, ROI, bitPPix)
        self.sizePerFileLabel.setText(str(sizeMax))
        
        cycleTime = self.testFramerateInt()
        durationPerFile = framePerFile*cycleTime
        self.durationPerFileLabel.setText(str(round(durationPerFile,2)))
    
    ### SAVING FOLDER CHOICE ###
    
    def browseSavingFolder(self):
        """
        Use QFileDialog to display a window and ask for a folder selection.
        """
        
        folderName = str(QFileDialog.getExistingDirectory(self, "Select Folder"))
        if path.isdir(folderName): #check that a directory was selected
            self.savingPath.clear()
            self.savingPath.insert(folderName)
        else:
            print('No folder selected')
            
    def arduinoSync(self):
        """
        Send informations about the coming sequence acquisition to the arduino
        inside each LED drivers
        """
        #Calculation of the time LED must be on
        exp = (self.mmc.getExposure()) # in ms
        #list containing each illumTime for each LED
        illumTime=[round(exp*(self.rExpRatio.value()),3),
                   round(exp*(self.gExpRatio.value()),3),
                   round(exp*(self.bExpRatio.value()),3)]
        rgbLedRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()]
        greenFrameInterval = self.gInterval.value()
        colorMode = self.rbColorBox.currentText()
        
        
        
        #Arduino sync via ArduinoTeensy package
        if self.rgbMode.isChecked():
            print 'rgbMode call'
            ledDriverNb=[0,1,2] #[Red, Green, Blue]
            for driverNb in ledDriverNb:
                #driver init
                driver = Arduino(driverNb)
                driver.synchronization(illumTime,  
                                       rgbLedRatio = rgbLedRatio)
                
        elif self.rbMode.isChecked():
            print 'rbMode call'
            ledDriverNb=[0,1,2] #[Red, Green, Blue]
            for driverNb in ledDriverNb:
                #driver init
                driver = Arduino(driverNb)
                driver.synchronization(illumTime,  
                                       greenFrameInterval = greenFrameInterval,
                                       colorMode = colorMode)

    
    ######################################
    #### Sequence acquisition section ####
    ######################################
    
    def paramCheck(self):
        """ 
        Check that the user is well informed about certains acquisition settings before launching the acquisition
        """
        run = True
        
        #Shutter mode check
        if mmc.getProperty(DEVICE[0], 'ElectronicShutteringMode')== 'Rolling':
            choice = QMessageBox.question(self, 'Shutter Mode',
                                                "Running acquisition in Rolling mode ?",
                                                QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                print("Running in Rolling mode")
                run = True
            else:
                print('Change mode in the other panel')
                run = False
                
        #Check that a directory was selected
        folderName=self.savingPath.text()        
        if run:
            print (folderName+'/'+self.experimentName.text())
            if not (path.isdir(folderName)) :
                emptyFolderMsg = QMessageBox.warning(self,"Empty saving Folder",
                                                     "Select a folder before running the experiment")
                print emptyFolderMsg
                run = False
            elif path.exists(folderName+'/'+self.experimentName.text()):
                choice = QMessageBox.question(self, 'Overwriting',
                                                "This experiment folder already exist, do you want to overwrite it ?",
                                                QMessageBox.Yes | QMessageBox.No)
                if choice == QMessageBox.Yes:
                    print("Overwriting")
                    run = True
                else:
                    print('Change the experiment name')
                    run = False
        return run
            
    def runCheck(self):
        """
        Check the parameters of the acquisiton before calling it.
        """
        if self.paramCheck():
            self.saveImageSeq()
    
    def saveImageSeq(self):
        """
        Get all informations from the GUI needed for setting up an acquisition.
        Then instanciate an object from the SequenceAcquisition class, and this
        object will handle the actual sequence acquisition.
        """
        
        #Get the trigger settings from the GUI
        triggerStart = self.startTriggerBox.isChecked()
        triggerStop = self.stopTriggerBox.isChecked()
        
        
        #Creation of a SequenceAcquisition class instance
        self.sequencAcq = SequenceAcquisition(self.mmc,self.labjack)
        print 'object initialized'
        self.sequencAcq.isFinished.connect(self.acquisitionDone)
        self.sequencAcq.nbFramesSig.connect(self.initProgressBar)
        self.sequencAcq.progressSig.connect(self.updateProgressBar)
        
        #Get experiment/acquisition settings from the GUI
        self.sequencAcq.experimentName = self.experimentName.text() #str
        self.sequencAcq.duration = self.experimentDuration.value() # float (seconds)
        self.sequencAcq.cycleTime = (self.testFramerateInt()) # int (seconds)
        self.sequencAcq.rgbLedRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] #list of int
        self.sequencAcq.maxFrames =self.framePerFileBox.value() #int
        self.sequencAcq.expRatio = [self.rExpRatio.value(),self.gExpRatio.value(),self.bExpRatio.value()]  #list float
        self.sequencAcq.greenFrameInterval = self.gInterval.value() #int
        self.sequencAcq.folderPath = self.savingPath.text() #str
        self.sequencAcq.colorMode = self.rbColorBox.currentText() #str
        
        self.sequencAcq.acquMode = "Run"
        if self.rgbMode.isChecked():
            self.sequencAcq.seqMode = "rgbMode"
        elif self.rbMode.isChecked():
            self.sequencAcq.seqMode = "rbMode"
        
        
        # At this point we want to allow user to stop/terminate the thread
        # so we enable that button
        self.abortBtn.setEnabled(True)
        # And we connect the click of that button to the built in
        # terminate method that all QThread instances have
        self.abortBtn.clicked.connect(self.sequencAcq.abort)
        
        if triggerStop:
            #--> reading an while looping for the image acquisition
            # input and when the signal goes high
            interruptAIN = 1
            stopSignalState = False
            waitToCheckSignal = 0.5
            
            stopTriggerMsg = QMessageBox()
            stopTriggerMsg.setIcon(QMessageBox.Warning)
            stopTriggerMsg.setText("Low SYNC signal detected")
            stopTriggerMsg.setWindowTitle("Aborted acquisition")
            
            #Instanciate a SignalInterrupt object to listen to the labjack and detect interrupt
            self.stopInterrupt = SignalInterrupt(self.labjack, interruptAIN, waitToCheckSignal, stopSignalState)
            self.stopInterrupt.stateReachedInterrupt.connect(self.sequencAcq.abort)
            self.stopInterrupt.stateReachedInterrupt.connect(stopTriggerMsg.exec_)
            self.abortBtn.clicked.connect(self.sequencAcq.abort)
            self.sequencAcq.isFinished.connect(self.stopInterrupt.abort)
            self.abortBtn.clicked.connect(self.stopInterrupt.abort)
            self.stopInterrupt.start()
        
        # We don't want to enable user to start another thread while this one is
        # running so we disable the start button.
        self.runSaveBtn.setEnabled(False)
        self.loopBtn.setEnabled(False)
        #Prepare each informations and file needed
        self.sequencAcq.sequencePreparation()
        if not triggerStart:
            # We have all the events we need connected we can start the thread 
            self.sequencAcq.start()
        else:
            interruptAIN = 1
            startSignalState = True
            waitToCheckSignal = 0.5
            
            startTriggerMsg = QMessageBox()
            startTriggerMsg.setIcon(QMessageBox.Warning)
            startTriggerMsg.setText("Labjack is ready to receive external signal")
            startTriggerMsg.setWindowTitle("Waiting for a SYNC signal")
            
            #Instanciate a SignalInterrupt object to listen to the labjack and detect interrupt
            self.startInterrupt = SignalInterrupt(self.labjack, interruptAIN, waitToCheckSignal, startSignalState)
            self.startInterrupt.stateReachedInterrupt.connect(self.sequencAcq.start)
            try:
                self.startInterrupt.stateReachedInterrupt.connect(startTriggerMsg.close)
            except:
                print ' no way to connect close fct'
            self.sequencAcq.isStarted.connect(self.startInterrupt.abort)
            self.startInterrupt.start() # start listening to the signal
            startTriggerMsg.exec_() #Pop window to prevent listenning to trigger
            
    
    def loopCheck(self):
        """
        Check the parameters of the acquisiton before calling it.
        """
        if self.paramCheck():
            self.loopAcquisition()
    
    def loopAcquisition(self):
        """
        Acquire images in a loop process, synchronized with a SYNC signal.
        """
        #Creation of a SequenceAcquisition class instance
        self.sequencAcq = SequenceAcquisition(self.mmc,self.labjack)
        print 'object initialized'
        self.sequencAcq.isFinished.connect(self.acquisitionDone)
        
        #Get experiment/acquisition settings from the GUI
        self.sequencAcq.experimentName = self.experimentName.text() #str
        self.sequencAcq.cycleTime = (self.testFramerateInt()) # int (seconds)
        self.sequencAcq.rgbLedRatio = [self.rRatio.value(),self.gRatio.value(),self.bRatio.value()] #list of int
        self.sequencAcq.maxFrames =self.framePerFileBox.value() #int
        self.sequencAcq.expRatio = [self.rExpRatio.value(),self.gExpRatio.value(),self.bExpRatio.value()] #float
        self.sequencAcq.greenFrameInterval = self.gInterval.value() #int
        self.sequencAcq.folderPath = self.savingPath.text() #str
        self.sequencAcq.colorMode = self.rbColorBox.currentText() #str
        
        self.sequencAcq.acquMode = "Loop"
        if self.rgbMode.isChecked():
            self.sequencAcq.seqMode = "rgbMode"
        elif self.rbMode.isChecked():
            self.sequencAcq.seqMode = "rbMode"
        
        # At this point we want to allow user to stop/terminate the thread
        # so we enable that button
        self.abortBtn.setEnabled(True)
        # And we connect the click of that button to the built in
        # terminate method that all QThread instances have
        self.abortBtn.clicked.connect(self.sequencAcq.abort)
        # We don't want to enable user to start another thread while this one is
        # running so we disable the start button.
        self.runSaveBtn.setEnabled(False)
        self.loopBtn.setEnabled(False)
        #Prepare experiment folder and config File
        self.sequencAcq.loopFolderPreparation()
        # We have all the events we need connected we can start the thread 
        self.sequencAcq.start()
    
    ##### Methods in charge of communication with SequenceAcquisition class instance ####
    def initProgressBar(self,nbFrames):
        """
        Initialize the progress bar in function of the nb of frames of the acquisition.
        """
        self.progressBar.setMaximum(nbFrames)
        
    def updateProgressBar(self,imageCount):
        """
        Update progress bar in function of the acquisition progress.
        """
        self.progressBar.setValue(imageCount+1)
    
    def acquisitionDone(self):
        """
        Udpate the GUI when an acquisition is finished.
        """
        #Reset progressBar
        self.progressBar.reset()
        #Change button state
        self.abortBtn.setEnabled(False)
        self.loopBtn.setEnabled(True)
        self.runSaveBtn.setEnabled(True)
    
    #############################    
    #### Live Histogram part ####
    #############################
    
    def oldHisto(self):
        """
        Function that calculate and display a histogram.
        """
        triggerMode = 'Internal (Recommended for fast acquisitions)'
        if self.triggerModeCheck(triggerMode):
            (mask, h_h, h_w, pixMaxVal, bin_width, nbins) = histoInit(mmc)
            cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
            cv2.namedWindow('Video')
            self.mmc.snapImage()
            g = self.mmc.getImage() #Initialize g
            self.mmc.startContinuousSequenceAcquisition(1)
            while True:
                    if self.mmc.getRemainingImageCount() > 0:
                        g = self.mmc.getLastImage()
                        rgb2 = cv2.cvtColor(g.astype("uint16"),cv2.COLOR_GRAY2RGB)
                        rgb2[g>(pixMaxVal-2)]=mask[g>(pixMaxVal-2)]*256 #It cannot be compared to pixMaxVal because it will never reach this value
                        cv2.imshow('Video', rgb2)

                    else:
                        print('No frame')

                    h = histoCalc(nbins, pixMaxVal, bin_width, h_h, h_w, g)
                    cv2.imshow('Histogram',h)

                    if cv2.waitKey(33) == 27:
                        break
                    if cv2.getWindowProperty('Video', 1) == -1: #Condition verified when 'X' (close) button is pressed
                        break
                    elif cv2.getWindowProperty('Histogram', 1) == -1: #Condition verified when 'X' (close) button is pressed
                        break

            cv2.destroyAllWindows()
            self.mmc.stopSequenceAcquisition()
            
            
    ##############################    
    #### Files splitting part ####
    ##############################
        
    ####CLASSIC FILE###
    def loadFolder(self):
        """
        Load a folder containing experiments.
        """    
        folderName = str(QFileDialog.getExistingDirectory(self, "Select a valid mouse folder [ID_...]"))
        if path.isdir(folderName):
            self.folderName.setText(folderName)
            self.classicAnalysisPath = folderName
            subDirectories = get_immediate_subdirectories(self.classicAnalysisPath)
            self.subDirList.clear()
            self.subDirList.addItems(subDirectories)
        else:
            print('No folder selected')
        

    def processRunExperiment(self):
        """
        Get the experiment folder name from the gui and call the split fction.
        Called when split channels button is pressed.
        """
        experimentFolder = self.subDirList.currentItem() 
        if experimentFolder :
            print 'item well selected'
            experimentName = experimentFolder.text()
            experimentFolder = self.classicAnalysisPath+'/'+experimentName
            processedFolderPath = experimentFolder+'/Processed'
            if not os.path.exists(processedFolderPath):
                os.makedirs(processedFolderPath)
            self.splitChannels(experimentName, experimentFolder, processedFolderPath)
        else:
            print 'Please, select a valid experiment folder' #TO DO : add window
    
    def processAllRunExperiments(self):
        """
        Get all the experiment names and call slit fct for each one
        """
        try:
            experimentsList = []
            for index in xrange(self.subDirList.count()):
                experimentsList.append(self.subDirList.item(index))
        except:
            print('cannot call this protected function')
        try:
            for experiment in experimentsList:
                experimentName = experiment.text()
                experimentFolder = self.classicAnalysisPath+'/'+experimentName
                processedFolderPath = experimentFolder+'/Processed'
                if not os.path.exists(processedFolderPath):
                    os.makedirs(processedFolderPath)
                self.splitChannels(experimentName, experimentFolder, processedFolderPath)
        except:
            print('Empty list of experiments')

    
    def splitChannels(self, filesName, filesFolder, processedFolderPath):
        """
        Concatenate all the .tif to segment them in blue, red and green channels.
        Create new .txt files for each channels containing the timestamps.
        """
        
        #print self.analysisPath
        print 'loading ', filesName,' in folder : ',filesFolder
        #experimentFolderPath = self.analysisPath+'/'+experimentFolderName
        #print experimentFolderPath
        filePath =filesFolder+'/'+filesName
        print filePath
        txtFile=filePath+'.txt'
        try:
            txtArray = load2DArrayFromTxt(txtFile,"\t")
        except:
            print 'error to convert txt to array'
        try:
            tifsPathList = getTifLists(filesFolder, filesName)
            print tifsPathList
        except:
            print 'error to get the tifs list'
        try:
            splitColorChannel(filesName, txtArray, tifsPathList, processedFolderPath)
        except:
            print 'error to split channels' 
    
    ####LOOP FILE###
    
    def loadLoopExp(self):
        """
        Load a loop folder experiment.
        """
        folderName = str(QFileDialog.getExistingDirectory(self, "Select a valid experiment folder generated by LOOP execution"))
        if path.isdir(folderName):
            self.experimentFolderName.setText(folderName)
            txtList = getTxtList(folderName, hideExt=True)
            if txtList:
                self.dataStimList.clear()
                self.dataStimList.addItems(txtList)
                self.loopAnalysisPath = folderName
            else:
                print('Wrong or empty folder')
        else:
            print('No folder selected')
            
    def loadStimSequence(self):
        """
        Load a .json file containing infromations about olfactory stimulation
        """
        selectedFile = QFileDialog.getOpenFileName(self, 'Open stim sequence file', filter=('JSON configuration file (*.json)'))
        #FileName contains the file name and the filter so we select only first component
        fileName=selectedFile[0]
        if path.isfile(fileName):
            self.stimDic = jsonFileLoading(fileName)
            try:
                valveList = self.stimDic["valveList"]
                stimNb = 1
                for valve in valveList:
                    self.stimList.addItem('S%(number)03d' % {"number": stimNb}+' : '+str(valve))
                    stimNb+=1
            except:
                print 'Json structure non valid'
        else:
            print('No file selected')
    
    def splitStimFiles(self):
        """
        Split channels from .tif file(s) and split .txt file from a single
        stimulation
        """
        stimName = self.dataStimList.currentItem() 
        if stimName :
            print 'item well selected'
            stimName = stimName.text()
            experimentFolder = self.loopAnalysisPath
            processedFolderPath = experimentFolder+'/'+stimName+'_processed'
            if not os.path.exists(processedFolderPath):
                os.makedirs(processedFolderPath)
            self.splitChannels(stimName, experimentFolder, processedFolderPath)
        else:
            print 'Please, select a stimulation file' #TO DO : add window
    
    def splitLoopExp(self):
        """
        Split channels from .tif file(s) and split .txt file from all stimulations
        and order them in odour folder
        """
        try:
            numOfVials = self.stimDic["numOfVials"]
            print "numOfVials ",numOfVials
            nOfTrials = self.stimDic["nOfTrials"]
            print "nOfTrials ",nOfTrials
            valveList = self.stimDic["valveList"]
            process = True
        except:
            print 'please select a correct json file'
            process=False
        ##verification that stimDic and stimFiles are loaded and have the same length
        if process and self.dataStimList.count()==self.stimList.count():
            #loop through each stim file and associate im
            for index in xrange(self.dataStimList.count()):
                stimName = self.dataStimList.item(index).text()
                print stimName
                #stimNb =int(stimName[-2:]) #take the last 2 char which are the stimNb
                odour = valveList[index]
                print 'odour : ',odour
                experimentFolder = self.loopAnalysisPath
                processedFolderPath = experimentFolder+'/OD'+str(odour)+'_processed'
                if not os.path.exists(processedFolderPath):
                    os.makedirs(processedFolderPath)
                self.splitChannels(stimName, experimentFolder, processedFolderPath)
                #copy the .txt with all metadat in the processed folder
                shutil.copy(experimentFolder+'/'+stimName+'.txt',processedFolderPath) 
            
                
                
                
        else:
            print 'select a stim sequence file'
        
    
    #################################
    #### Odour Map Creation Part ####
    #################################
    
    def loadExpOdFolder(self):
        """
        Load an odour folder containing each color channel for a stimulation
        (bot .tif and .txt channel)
        """
        
        folderName = str(QFileDialog.getExistingDirectory(self, "Select an experiment folder"))
        if path.isdir(folderName):
           self.expFolderO.setText(folderName)
           self.expFolderOPath = folderName
           subDirectories = get_immediate_subdirectories(folderName)
           if len(subDirectories) == 0:
               print "Don't forget to split files into odours folder"
           else:   
               self.odourFoldersList.clear()
               self.odourFoldersList.addItems(subDirectories)
               self.odourFoldersList.itemClicked.connect(self.mapCreationUpdate)
               
    def mapCreationUpdate(self, listItem):
        """
        Take an odour folder in argument and update the informations displayed 
        in the GUI about the processing parameters.
        """
        try:
            odourFolder = listItem.text()
            print odourFolder
            print self.expFolderOPath+'/'+odourFolder
            odourMap = OdourMap(self.expFolderOPath+'/'+odourFolder)
            print 'odourMap object well instanciate'
            self.baselineLength.setMaximum(odourMap.baselineLenMax)
            self.stimLength.setMaximum(odourMap.stimLenMax)
            (rEdge,fEdge) = odourMap.rAndFEdges[0][0] #Take the rEdge and fEdge of the red text file and first stim
            print rEdge,fEdge
            self.stimStartLabel.setText(str(rEdge))
            self.stimEndLabel.setText(str(fEdge))
        except:
            print 'No way to initialize the odourFolder object'
    
    def createOdourMap(self):
        """
        Create odour maps for each of the selected files on the computer.
        """
        selectedOdours = self.odourFoldersList.selectedItems()
        odour = selectedOdours[0]
        for odour in selectedOdours:
            odour = odour.text()
            print odour
            odourMap = None
            try:
                odourMap = OdourMap(self.expFolderOPath+'/'+odour)
            except:
                print 'ERROR : please select a valid odour folder'
            if odourMap is not None:
                odourMap.baselinLen = self.baselineLength.value()
                odourMap.stimLen = self.stimLength.value()
                odourMap.redProcess = self.redProcessBox.isChecked()
                odourMap.blueProcess = self.blueProcessBox.isChecked()
                odourMap.start()
            
    
    
    #################################
    #### Common utility function ####
    #################################
    
    def reconnect(self, signal, newhandler=None, oldhandler=None):
        """
        Deconnect a signal and reconnect it to another handler function.
        Source : https://stackoverflow.com/questions/21586643/pyqt-widget-connect-and-disconnect
        """
        while True:
            try:
                if oldhandler is not None:
                    signal.disconnect(oldhandler)
                else:
                    signal.disconnect()
                print 'disconnection OK'
            except TypeError:
                break
        if newhandler is not None:
            signal.connect(newhandler)
            print 'new connection ok'
    
    def closeEvent(self, event):
        """
        Executed when close button of the main window is clicked.
        Ask for closing and close properly the program.
        """
        # Close all before closing the main window
        closingChoice = QMessageBox.question(self, 
                                             'Close Confirmation',
                                             "Exit ?",
                                             QMessageBox.Yes | QMessageBox.No)
        
        if closingChoice == QMessageBox.Yes: # UNLOAD DEVICES before closing the program
            try:
                self.sequencAcq.abort()
                time.sleep(2) #Ensure all is well closed
            except:
                print('No sequenceAcqu running or impossible to abort it')
            self.unloadDevices()
            event.accept() # let the window close
        else:
            event.ignore()


##Launching everything
if __name__ == '__main__':
    
    """MicroManager Init"""
    mmc = MMCorePy.CMMCore()
    
    """Camera Init"""
    DEVICE = camInit(mmc) # TO FIX, give DEVICE at some function only
    
    """Labjack init"""
    labjack = labjackInit()
    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    #Change the window Icon
    app.setWindowIcon(QtGui.QIcon('OMMI_colours.png'))
    #Give an ID to the running application to separate it from python and show a different icon in the taskbar
    #source:https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105
    myappid = u'johnstonlab.OMMI.V2' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    window = isoiWindow(mmc, DEVICE, labjack)
    window.show()
    sys.exit(app.exec_())