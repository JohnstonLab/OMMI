# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 16:06:44 2019

@author: Louis Vande Perre

File containing the waiting for a signal thread.
"""
from PyQt5.QtCore import QThread, pyqtSignal
import threading

####functions import
from Labjack import readSignal

class SignalInterrupt(QThread):
    """
    An instance of this class will listen to a designated signal and emit pyqtSignal to interrupt a running thread or task
    """
    interrupt = pyqtSignal(bool)
    stateReachedInterrupt =pyqtSignal()
    
    def __init__(self, labjack, channel, waitTimeSeconds=0.5, waitedState = None, parent=None):
        QThread.__init__(self,parent)
        self.labjack = labjack
        self.channel = channel
        self.waitTimeSeconds = waitTimeSeconds
        self.waitedState = waitedState
        self.running = True
        print 'S interrupt created with scan time : ', self.waitTimeSeconds
    
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
        if signalValue > 2.4:
            state = True
        if signalValue < 0.8:
            state = False
        return state
    
    def _checkWantedState(self, signalState):
        """
        Emit an interrupt signal if the state reached is the expected one.
        """
        if signalState == self.waitedState:
            self.stateReachedInterrupt.emit()
            print 'Interrupt accepted'
        else:
            print 'Interrupt rejected (non expected state)'
    
    def run(self):
        """
        Default function of any QThread object
        Called by classInstance.start() to launch the thread
        """
        print ('Run fct of Signal Interrupt instance called')
        
        signalPrevState = self._signalState(readSignal(self.labjack, self.channel))
        
        ticker = threading.Event()
        while (not ticker.wait(self.waitTimeSeconds)) and (self.running):
            signalState = self._signalState(readSignal(self.labjack, self.channel))    
            if signalPrevState != signalState:
                    self.interrupt.emit(signalState)
                    print 'interrupt detected'
                    if self.waitedState != None:
                        self._checkWantedState(signalState)
                    print 'interrupt'
            signalPrevState =self._signalState(readSignal(self.labjack, self.channel)) 
        print 'run fct of Interrupt done'
    
    def abort(self):
        """
        Stop the main thread if no interrupt detected.
        """
        self.running = False
        
