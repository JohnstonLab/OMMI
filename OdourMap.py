# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 16:47:58 2019

@author: Louis Vande Perre

class for Map segmentation
"""

#Packages import
from PyQt5.QtCore import QThread

#package import
import ParsingFiles
import numpy as np 
import tifffile
import matplotlib.pyplot as plt
from skimage import filters, transform, util
import cv2

class OdourMap(QThread):
    """
    OdourMap object are created from pre-parsed data
    """
    
    mathOperation = ["divide","substract"]
    
    def __init__(self, odourFolder,parent=None):
        QThread.__init__(self,parent)
        
        self.odourFolder = odourFolder
        self.txtList = ParsingFiles.getTxtList(odourFolder) #WARNING : only the .txt name
        self.redTifs = ParsingFiles.getTifLists(odourFolder, color ='R') #full path of the file
        print self.redTifs
        self.blueTifs = ParsingFiles.getTifLists(odourFolder, color ='B')
        print self.blueTifs
        self.stimNb = self._stimNbCalculation(self.txtList)
        print 'stimNb :', self.stimNb 
        #create a matrix of tuples which will contain (rEdge,fEdge) for each 
        #images stacks. Each row of this matrix correspond to a stim and each
        # column correspond to a color (column 0 > RED, column 1 > BLUE)
        self.rAndFEdges = np.zeros((self.stimNb,2), dtype='i,i')
        self.baselineLenMax = 10000
        self.stimLenMax = 10000
        self.stimLen = None
        self.baselinLen = None
        
        #Filtering parameter
        self.filterSize = (3,3) #default value
        
        #Downsampling the image
        self.rescaleRatio = 0.5 #default value
        
        self.mathOperation = OdourMap.mathOperation[0]
        
        self.redProcess = False
        self.blueProcess = False
        
    def __del__(self):
        self.wait()
        
    def getFilterSize(self):
        """
        Return the filter size of the odour map object
        """
        return self.filterSize
    
    def setFilterSize(self, filterSize):
        """
        Set the filter size of the odour map object
        """
        if type(filterSize) == tuple:
            self.filterSize = filterSize
        elif type(filterSize) == int:
            self.filterSize = (filterSize,filterSize)
        else:
            print 'Wrong size type, filter size value : ',self.getFilterSize()
    
    def getRescaleRatio(self):
        """
        Return the rescaling ratio of the odour map object
        """
        return self.filterSize
    
    def setRescaleRatio(self, rescaleRatio):
        """
        Set the rescaling ratio of the odour map object
        """
        if type(rescaleRatio) == float:
            self.rescaleRatio = rescaleRatio
        else:
            print 'Wrong size type, rescaling ratio value : ',self.getRescaleRatio()
            
    def setBaselineLen(self, baselineLen):
        """
        Set the baseline length of the odour map object
        """
        if type(baselineLen) == int:
            self.baselinLen = baselineLen
        else:
            print 'Wrong size type, baseline length value : ',self.baselinLen
            
    def setStimLen(self, stimLen):
        """
        Set the stimulation length of the odour map object
        """
        if type(stimLen) == int:
            self.stimLen = stimLen
        else:
            print 'Wrong size type, stimulation length value : ',self.stimLen
        
    def bAndSMaxLength(self):
        """
        Scan each txt (for blue and red channels)in the odour folder and 
        determine the maximum stimulation length and baseline length
        """
        stimNbBlue=0
        stimNbRed=0
        for txt in self.txtList:
            if txt[-5:-4] == 'B': #take the last characters of the filename (without the extension)
                self._edgeSignalDetection(txt, stimNbBlue, 1)
                stimNbBlue+=1
                
            elif txt[-5:-4] == 'R': #take the last characters of the filename (without the extension)
                self._edgeSignalDetection(txt, stimNbRed, 0)
                stimNbRed+=1
                
    
    def _edgeSignalDetection(self, txt, stimNb, color):
        """
        Scan a single stimulation txt file and return the stim and baseline
        length
        """
        try:
            txtArray = ParsingFiles.load2DArrayFromTxt(self.odourFolder+'/'+txt, '\t')
            #time = txtArray[:,0]
            odourValve = txtArray[:,1]
            #calculation of the baseline and stim lenght
            stimStart = 0
            frameCounter = 0
            prevValue = 0 #Suppose that each txt begin with low stim
            for value in odourValve:
                if prevValue < value:
                    rEdgeValue = frameCounter
                elif prevValue > value:
                    fEdgeValue = frameCounter
                    baselineLen =  rEdgeValue-stimStart
                    stimLen = fEdgeValue - rEdgeValue
                    if baselineLen < self.baselineLenMax:
                        self.baselineLenMax = baselineLen
                        print 'baselineMax : ',self.baselineLenMax
                    if stimLen < self.stimLenMax:
                        self.stimLenMax = stimLen
                        print 'stim max : ',self.stimLenMax
                    try:    
                        self.rAndFEdges[stimNb,color] = (rEdgeValue,fEdgeValue)
                    except:
                        print 'array trouble'
                    
                frameCounter+=1
                prevValue=value
        except:
            print ('wrong txt file structure')
        
            
    def _stimNbCalculation(self, txtList):
        """
        Scan folder and count the number of txt per channels i.e. the number of stim
        """
        stimNb = 0
        for txt in self.txtList:
            if txt[-5:-4] == 'B': #Arbitrary we use the blue channel
                stimNb+=1
        return stimNb
                
    def _imagesProcessing(self, tif):
        """
        Process each images of the stack contained in one .tif file.
        Warning data type :
        https://scikit-image.org/docs/dev/user_guide/data_types.html#data-types
        """
        tif32 = util.img_as_float32(tif)
        N = tif32.shape[0]
        tifAvg = None
        imCount = 0
        for image in tif32:
            print image.shape
            im = filters.median(image, np.ones(self.filterSize))
            try:
                im = transform.rescale(im, self.rescaleRatio, anti_aliasing=True)
                print im.shape
            except:
                print 'failed rescale'
            if tifAvg is not None :
                tifAvg += im/N
            else:
                h,w = im.shape
                tifAvg = np.ones((h,w), np.float32) 
                tifAvg += im/N
            print 'image ',imCount,' processed'
            imCount+=1
        return tifAvg
            
    
    def _tifProcessing(self, tif, stimNb, color):
        """
        Apply ro whole pipeline to a tif containing frames for 1 stimulation
        """
        tifArray = tifffile.imread(tif)
        print 'tif shape : ', tifArray.shape
        rEdge = self.rAndFEdges[stimNb,color][0]
        fEdge = self.rAndFEdges[stimNb,color][1]
        if self.baselinLen :
            baseline = tifArray[rEdge-self.baselinLen: rEdge]
        else:
            baseline = tifArray[rEdge-self.baselineLenMax: rEdge]
        if self.stimLen:
            stim = tifArray[fEdge-self.stimLen:fEdge]
        else:
            stim = tifArray[fEdge-self.stimLenMax:fEdge]
        print baseline.shape, stim.shape
        baselineAvg = self._imagesProcessing(baseline)
        stimAvg = self._imagesProcessing(stim)
        
        if self.mathOperation == OdourMap.mathOperation[0]: #divide
            odMap = (stimAvg/baselineAvg)
        elif self.mathOperation == OdourMap.mathOperation[1]: #substract
            odMap= stimAvg-baselineAvg
        
        print odMap
        tifffile.imsave(self.odourFolder+'/stim_c%i_S%i.tif' %(color,stimNb), stimAvg)
        print self.odourFolder+'/stim_c%i_S%i.tif' %(color,stimNb)
        tifffile.imsave(self.odourFolder+'/baseline_c%i_S%i.tif' %(color,stimNb), baselineAvg)
        print self.odourFolder+'/baseline_c%i_S%i.tif' %(color,stimNb)
        tifffile.imsave(self.odourFolder+'/map_c%i_S%i.tif' %(color,stimNb),odMap)
        print self.odourFolder+'/map_c%i_S%i.tif' %(color,stimNb)
        
#        cv2.namedWindow('Stim AVG')
#        cv2.namedWindow('Baseline AVG')
#        cv2.imshow('Stim AVG', stimAvg)
#        cv2.imshow('Baseline AVG', baselineAvg)
#        cv2.namedWindow('odour map')
#        cv2.imshow('odour map', odMap)
#        
#        while(True):
#            if cv2.waitKey(33) == 27:
#                break
#            if cv2.getWindowProperty('Stim AVG', 1) == -1: #Condition verified when 'X' (close) button is pressed
#                break
#            if cv2.getWindowProperty('Baseline AVG', 1) == -1: #Condition verified when 'X' (close) button is pressed
#                break 
#        cv2.destroyAllWindows()
    
    
    def run(self):
        """
        Contains the main part of the process (allowing th GUI to response)
        """
        print('run fct of the odourMap class called')
        
        if self.redProcess :
            print 'red process'
            stimNb=0
            color=0
            for tif in self.redTifs:
                print 'processing of : ', tif
                self._tifProcessing(tif, stimNb, color)
                stimNb+=1
        if self.blueProcess :
            print 'blue process'
            stimNb=0
            color=1
            for tif in self.blueTifs:
                print 'processing of : ', tif
                self._tifProcessing(tif, stimNb, color)
                stimNb+=1
        
        
if __name__ == '__main__':
    
    print 'test'
    odourMap = OdourMap('C:/data_OMMI/ID723/10pc/OD1_processed')
    odourMap.bAndSMaxLength()
    odourMap.baselinLen = 100
    odourMap.stimLen = 150
    odourMap.redProcess = True
    odourMap.mathOperation="divide"
    odourMap.start()
    