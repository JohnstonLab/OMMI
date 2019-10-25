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

class OdourMap(QThread):
    """
    OdourMap object are created from pre-parsed data
    """
    
    def __init__(self, odourFolder,parent=None):
        QThread.__init__(self,parent)
        
        self.odourFolder = odourFolder
        self.txtList = ParsingFiles.getTxtList(odourFolder)
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
        if type(filterSize) == tuple or type(filterSize) == int:
            self.filterSize = filterSize
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
                    print 'Stim nb : ', stimNb,' and color : ', color
                    try:    
                        self.rAndFEdges[stimNb,color] = (rEdgeValue,fEdgeValue)
                    except:
                        print 'array trouble'
                    print self.rAndFEdges
                    
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
                
    
    def run(self):
        """
        Contains the main part of the process (allowing th GUI to response)
        """
        print('run fct of the odourMap class called')
        
        if self.redProcess :
            print 'red process'
        if self.blueProcess :
            print 'blue process'
        
        
if __name__ == '__main__':
    
    print 'test'
    odourMap = OdourMap('C:/data_OMMI/01pc/OD1_processed')
    odourMap.bAndSMaxLength()
    