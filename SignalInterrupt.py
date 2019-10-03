# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 16:06:44 2019

@author: Louis Vande Perre

File containing the waiting for a signal thread.
"""
from PyQt5.QtCore import QThread, pyqtSignal
import threading

####functions import
from labjack import readSignal

class SignalInterrupt(QThread):
    """
    An instance of this class will listen to a designated signal and emit pyqtSignal to interrupt a running thread or task
    """
    interrupt = pyqtSignal(bool)
    
    def __init__(self, labjack, channel, parent=None):
        QThread.__init__(self,parent)
        self.labjack = labjack
        self.channel = channel
    
    def __del__(self):
        self.wait()
    
    def _signalState(self, signalValue):
        """
        Take the value of the signal given in argument and return a boolean
        to describe the state of the signal.
        HIGH (>2.4) > True
        LOW (<0.8) > False
        """
        state = None
        print'measure taken'
        if signalValue > 2.4:
            state = True
        if signalValue < 0.8:
            state = False
        return state
    
    def run(self):
        """
        Default function of any QThread object
        Called by classInstance.start() to launch the thread
        """
        print ('Run fct of Signal Interrupt instance called')
        
        signalPrevState = self._signalState(readSignal(self.labjack, self.channel))
        
        WAIT_TIME_SECONDS = 0.5
        ticker = threading.Event()
        while not ticker.wait(WAIT_TIME_SECONDS):
            signalState = self._signalState(readSignal(self.labjack, self.channel))    
            if signalPrevState != signalState:
                    self.interrupt.emit(signalState)
                    print 'interrupt'
        print 'run fct done'
        
