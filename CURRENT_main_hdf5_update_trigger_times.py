"""
at binn 1x1: 1 micron = 1.8348 pix
at binn 4x4: 1 micron = 7.3 pix


update:
    add/remove selected epoch row
    load/save epoch list file
    exposure doesnt change anymore during run
    record respiration in a txt file at each trial

to do:
    green frame issue
    loading bar
    tidy up code and comment
    separate in different python files
    trackbar min/max/step for exposure
"""


from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
import serial

from OII_hdf5 import *
from OII_ui import Ui_MainWindow

import sys
import os 
os.chdir("C:\Program Files\Micro-Manager-1.4")
# makes "from OII_ui import Ui_MainWindow" fails, OI_ui.py and OI_ui.ui added to the folder to fix that
print os.getcwd()

import time
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import MMCorePy #Micromanager
import u3 #LabJack

import matplotlib
import matplotlib.pyplot as plt
import cv2
import cv2.cv as cv
from time import time
import numpy as np
import pickle
from tifffile import imsave,imshow,imread
from datetime import date
import serial #arduino

import Tkinter
import tkFileDialog
import os
import os.path as pth
import scipy

date = str(date.today())
savepath="C:/data_OIIS/"+date[2:4]+date[5:7]+date[8:10]

if not os.path.exists(savepath):
    os.makedirs(savepath)

#trackbar
div=100
step=1/float(div)

#threshold red mask, saturated pixels
thd=65500


DEVICE = ['Zyla','AndorSDK3','Andor sCMOS Camera'] #name, descriptio, Name


#Exposure (just here to keep it as global var)
exp=2
expMin=0.0277
expMax=500.00

#Acquisition Window (Full Image 128x128 512x512 1392x1040 1920x1080 2048x2048)
AcqWindow= "Full Image"

#PixelReadoutRate (200 MHz - lowest noise  560 MHz - fastest readout)
PixRR="560 MHz - fastest readout"

#Binning (1x1 2x2 4x4 8x8 )
binn="4x4"

#Sensitivity/DynamicRange 
#( 12-bit (high well capacity) 12-bit (low noise) 16-bit (low noise & high well capacity))
bit= "16-bit (low noise & high well capacity)"

#



#red/green leds
toggle_r=False
toggle_g=False
red_lj=5
green_lj=4

#valves
toggle_v1=False
toggle_v2=False
v1_lj=6 #dac0
v2_lj=7 #dac1


#list containing epochs items as list (name,exp,led,odor,duration)
epoch_seq = [] 
frames=[]
timestamps = []
meta = []
meta_index=[]
m_i_trial=[]
boxes=[]

## Boolean variable that will represent 
## whether or not the arduino is connected
connected = False

## establish connection to the serial port that your arduino 
## is connected to.
locations=['COM4']

for device in locations:
    try:
        print "Trying...",device
        ser = serial.Serial(device, 9600)
        break
    except:
        print "Failed to connect on",device

## loop until the arduino tells us it is ready
#while not connected:
    #serin = ser.read()
    #connected = True

data = [0]

def update():
    global curve, data
    line = ser.readline()
    data.append(int(line))
    xdata = np.array(data, dtype='float64')
    curve.setData(xdata)
    app.processEvents()

def onmouse(event, x, y, flags, params):
    # global img
    global down
    global crop


    if event == cv.CV_EVENT_LBUTTONDOWN:
         down=True

         print 'Start Mouse Position: '+str(x)+', '+str(y)
         sbox = [x, y]
         boxes.append(sbox)
#         rect_start=(boxes[0][0],boxes[0][1])
#         rect_end=(boxes[-1][0],boxes[-1][1])
#         color=(100,255,100)
#         cv2.rectangle(img,rect_start,rect_end,color)
#         cv2.imshow("mouse",img)
         # print count
         # print sbox

    elif event == cv.CV_EVENT_LBUTTONUP:
        down=False
        print 'End Mouse Position: '+str(x)+', '+str(y)
        ebox = [x, y]
        boxes.append(ebox)
        print boxes
        crop = img[boxes[-2][1]:boxes[-1][1],boxes[-2][0]:boxes[-1][0]]

        cv2.imshow('crop',crop)
        rect_start=(boxes[-2][0],boxes[-2][1])
        rect_end=(boxes[-1][0],boxes[-1][1])
        color=(100,255,100)
        cv2.rectangle(img,rect_start,rect_end,color)
        cv2.imshow('real image',img)
        k =  cv2.waitKey(0)
        if ord('r')== k:
            cv2.imwrite('Crop'+str(t)+'.jpg',crop)
            print "Written to file"

def crop_w_mouse(img):
        
        print "crop"
        down = False
    
        
        while(1):
            cv2.namedWindow('real image')
            cv.SetMouseCallback('real image',onmouse, 0)
            cv2.imshow('real image', img)
            if cv2.waitKey(33) == 27:
                cv2.destroyAllWindows()
                break

                
        x= boxes[-2][0]
        y= boxes[-2][1]
        w= boxes[-1][0] - x
        h= boxes[-1][1] - y
        print "selectROI x "+str(x)+" y "+str(y)+" w "+str(w)+" h "+str(h)
        mmc.setROI(x,y,w,h)
        
def crop_w_mouse_live(img):
        
        cv2.namedWindow('Video')
        mmc.startContinuousSequenceAcquisition(1)
        while True:
                img = mmc.getLastImage()
                if mmc.getRemainingImageCount() > 0:
                    img = mmc.getLastImage()
                    cv2.namedWindow('real image')
                    cv.SetMouseCallback('real image',onmouse, 0)
                    cv2.imshow('real image', img)
                else:
                    print('No frame')
                if cv2.waitKey(32) >= 0:
                    break
        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()
        

                
        x= boxes[-2][0]
        y= boxes[-2][1]
        w= boxes[-1][0] - x
        h= boxes[-1][1] - y
        print "selectROI x "+str(x)+" y "+str(y)+" w "+str(w)+" h "+str(h)
        mmc.setROI(x,y,w,h)



def saveAsMultipageTif_inter(datap,path,namep,m,k=512): ##TO FIX
    #k -> number of page per tif
    
    nFrames=datap.shape[0]+1
    n=m+1
    #datap=datap.astype('uint16')
    
    if not os.path.exists(path+'/'+namep+'/raw/'):
        os.makedirs(path+'/'+namep+'/raw/')

    #d = np.asarray(descri)
    namepp=namep#os.path.split(path)[1]+'_' #get the name of the subfolder
    print "nFrames "+str(nFrames)+" m "+str(m)
    for i in range(0,nFrames/k):
        print "XXX saving tiff "+str(m+i+1)
        image = datap[i*k:(i*k)+k,:,:]
        filename = path+'/'+namep+'/raw/'+namepp+'%(number)04d.tif' % {"number": m+i+1}
        imsave(filename, image)#,description =d[i*k:(i*k)+k])
        n=m+i+1
    #print "test2"
        
    if (nFrames % k > 0 ): #buggy ???        
        print "XXX saving tiff "+str(n+1)
        image = datap[nFrames-(nFrames % k):nFrames-1]
        filename = path+'/'+namep+'/raw/'+namepp+'%(number)04d.tif' % {"number": n+1}
        imsave(filename, image)#,description =d[nFrames-(nFrames % k):nFrames-1])
        n+=1
    #print "test3"
    return n
    
def runEpoch(mmc,device,rep):
    import time
    
    global epoch_seq #epochs items as list (name,exp,led,odor,duration,noRec)
    global meta_index # list: epoch name, start frame, end frame
    
    namep=window.path.text()
    print "create hdf5" 
    hdfpath = createHdf5andClose(namep,savepath)
    
    
    n_epoch=len(epoch_seq)
    total =0
    epoch_times =[]
    
    eps = 0.005 #delay... error in time passed
    lj_delay = 0#0.012
    count = 1 #epoch 0 effectuated before loop
    m=0 #tiff saving index
    namep=window.path.text()
    print "namep..."+str(namep)

    window.progressBar.setMinimum(0)
    
    window.progressBar.setMaximum(n_epoch+(rep-1)*n_epoch)

    print str(n_epoch)
    for i in range(n_epoch):
        total += epoch_seq[i][4]
        epoch_times.append(total)
    print str(n_epoch)+" epochs"
    print "should take "+str(total)+"s and repeated "+str(rep)+" time(s)"

    mmc.prepareSequenceAcquisition('Zyla')
    #print "preparing sequence acquisition took", time.clock()-start, "seconds"                                         
    
#    cv2.namedWindow('Video')
    
    text_file_globalTime = open(savepath+"/globalTime"+namep+".txt", 'w')
    #text_file_globalTime.write(str(time.clock()-start)+",  "+ser.readline()+"\n")
    
    
    for i in range(rep): #LOOP FOR TRIALS
            print "trial "+str(i+1)
            text_file = open(savepath+"/respi"+namep+"_trial_"+str(i+1)+".txt", 'w')
            text_file_globalTime.write( str(time.time())+",  "+str(i+1)+"\n")
            frame_i=0
                         
            #mmc.setProperty(DEVICE[0], 'Exposure', epoch_seq[0][1])
            setLed(device,epoch_seq[0][2])
            setOdor(device,epoch_seq[0][3])
            mmc.initializeCircularBuffer()                          
            mmc.startContinuousSequenceAcquisition(10)
            
            start=time.clock()  

            while time.clock()-start < total:
                if  mmc.getRemainingImageCount()>0 :
                    im = mmc.popNextImage()
                    #im = mmc.getLastImage()
                    #cv2.imshow('Video', im)  
                    #raw_input("pause")   
                    frames.append(im)
                    timestamps.append(time.clock()-start) #0.6s from start !!!
                    meta.append( (epoch_seq[count-1], i)) 
                
                if  (count < n_epoch) and (time.clock()-start+eps > epoch_times[count-1]) :
                    print "count "+str(count)
                    print epoch_seq[count-1][0]

                    print frame_i
                    print len(frames)-1
                    #mmc.setProperty(DEVICE[0], 'Exposure', epoch_seq[count][1])
                    setLed(device,epoch_seq[count][2])
                    setOdor(device,epoch_seq[count][3])
                    window.progressBar.setValue(count+i*n_epoch)
                    
#                 #saving index of previous epoch (name,start frame, end frame)
#                    frame_f=len(frames)-1
#                    meta_index.append((epoch_seq[count-1][0],frame_i,frame_f))
#                    frame_i=len(frames)
                    
                    if epoch_seq[count-1][5] == 0 :
                        frame_f=len(frames)-1
                        meta_index.append((epoch_seq[count-1][0],frame_i,frame_f))
                        frame_i=len(frames)
#                        nrec = 0
#                        mmc.stopSequenceAcquisition()
#                        mmc.clearCircularBuffer() 
                    if (epoch_seq[count][5] == 1):
                        print "stop recording "+str(epoch_seq[count][4])+ "sec"
                        time.sleep(epoch_seq[count][4])
                        mmc.clearCircularBuffer()
                        #meta_index.pop()

#                        if epoch_seq[count-1][5] == 1:
#                            mmc.initializeCircularBuffer()   
#                            mmc.startContinuousSequenceAcquisition(10)
#                            nrec=1                    
                    count += 1
                if ser.inWaiting() :
                            text_file.write(str(time.clock()-start)+",  "+ser.readline()+"\n")
#                if cv2.waitKey(1) >= 0:
#                    break
            frame_f=len(frames)-1
            meta_index.append((epoch_seq[count-1][0],frame_i,frame_f))
            frame_i=len(frames)
            
            m_i_trial.append(meta_index)
            meta_index=[]
            
            window.progressBar.setValue(n_epoch+i*n_epoch)
            #reset
            device.setFIOState(green_lj, 0)
            device.setFIOState(red_lj, 1)
            #device.setFIOState(v1_lj, 0)
            #device.setFIOState(v2_lj, 0)
            DAC0_VALUE = device.voltageToDACBits(0, dacNumber = 0, is16Bits = False)
            device.getFeedback(u3.DAC0_8(DAC0_VALUE))        
            DAC1_VALUE = device.voltageToDACBits(0, dacNumber = 1, is16Bits = False)
            device.getFeedback(u3.DAC1_8(DAC1_VALUE))       
                      
            print str(total)+"s acquisition took", time.clock()-start, "seconds"
            
            mmc.stopSequenceAcquisition()
            mmc.clearCircularBuffer() 
            if i < rep: #end of an epoch
                    #time spent savong files
                    savingTime=time.time()
                    #print "saving tiff.."+str(len(frames))+" frames"
                    #namep=window.path.text()
                    framesnp = np.asarray(frames)
                    
                    #display avg green
                    print "save green"+str(i)+" in "+savepath
                    scipy.misc.imsave(savepath+'/green'+str(i)+'.jpg', np.mean(framesnp[0:20],axis=0))
                    #plt.imshow(np.mean(framesnp[0:20],axis=0))
                    
                    #saveAsMultipageTif(framesnp,savepath,namep,meta,k=512)#
                    #m = saveAsMultipageTif_inter(framesnp,savepath,namep,m)
                    #print "number of tiff files :"+str(m)
                    print "save trial hdf5"
                    print m_i_trial[-1]
                    print i+1
                    hdfs=saveTrialHdf5andClose(hdfpath,framesnp,m_i_trial[-1],i+1,epoch_seq) #modified added epoch
                    print "closing hdfs"
                    hdfs.close()
                    print "closed"
                    #print "save respiratory signal"
                    # text_file = open("respi"+".txt", 'w')
                    print "empty frames list.."
                    frames[:]=[]
                    text_file.close()
                    timeSpentSaving=time.time()-savingTime
                    newDelay=window.dur_2.value()-timeSpentSaving
                    print "in total wating for "+str(window.dur_2.value())+" s"
                    print "after time spent saving wating for "+str(newDelay)+" s"
                    if (newDelay>0):
                        time.sleep(newDelay)
            count =1
    
    #cv2.destroyAllWindows()
                                

    
    #print "nOfFrames :"+str(len(frames)) 
    print "exposure was", mmc.getProperty('Zyla','Exposure')                                               
    print "Framerate was", mmc.getProperty('Zyla','FrameRate')             
    print "saving metadata, timestamps and comments"
    
    if not os.path.exists(savepath+"/"+namep):
        os.makedirs(savepath+"/"+namep)
    
    with open(savepath+"/"+namep+"/epoch.p", "wb") as fp:   #Pickling
        pickle.dump(epoch_seq, fp)
    with open(savepath+"/"+namep+"/comment.p", "wb") as fpp:   #Pickling
        pickle.dump(window.comment.toPlainText(), fpp)
    with open(savepath+"/"+namep+"/timestamps.p", "wb") as fppp:   #Pickling
        pickle.dump(timestamps, fppp)
    with open(savepath+"/"+namep+"/meta.p", "wb") as fppp:   #Pickling
        pickle.dump(meta, fppp)
    with open(savepath+"/"+namep+"/m_i_trial.p", "wb") as fppp:   #Pickling
        pickle.dump(m_i_trial, fppp)

    print "restart kernel to be safe"
    
    text_file_globalTime.close()
    print "global time txt closed"

    
    window.progressBar.setValue(0)       
    


def setOdor(device,odor):
    if odor == 0:
        #device.setFIOState(v1_lj, 0)
        DAC0_VALUE = device.voltageToDACBits(0, dacNumber = 0, is16Bits = False)
        device.getFeedback(u3.DAC0_8(DAC0_VALUE))   
    else :
        if odor == 1 :
            #device.setFIOState(v2_lj, 0)
            DAC1_VALUE = device.voltageToDACBits(0, dacNumber = 1, is16Bits = False)
            device.getFeedback(u3.DAC1_8(DAC1_VALUE))   
            #device.setFIOState(v1_lj, 1)    
            DAC0_VALUE = device.voltageToDACBits(5.5, dacNumber = 0, is16Bits = False)
            device.getFeedback(u3.DAC0_8(DAC0_VALUE))  
        else:
            #device.setFIOState(v2_lj, 1)
            DAC1_VALUE = device.voltageToDACBits(5.5, dacNumber = 1, is16Bits = False)
            device.getFeedback(u3.DAC1_8(DAC1_VALUE))  
            #device.setFIOState(v1_lj, 1)
            DAC0_VALUE = device.voltageToDACBits(5.5, dacNumber =0, is16Bits = False)
            device.getFeedback(u3.DAC0_8(DAC0_VALUE))  
    print "set odor to: "+str(odor)
    
def setLed(device,color):
    if color == 0:
        device.setFIOState(red_lj, 0)
        device.setFIOState(green_lj, 0)
    else :
        if color == 1 :
            device.setFIOState(red_lj, 0)
            device.setFIOState(green_lj, 1)    
        else:
            device.setFIOState(green_lj, 0)
            device.setFIOState(red_lj, 1)
    print "set led to: "+str(color)
    
    



class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('OII_ui.ui', self)
        
        # Connect buttons 
        
        self.LiveBtn.clicked.connect(self.LiveFunc)
        self.SnapBtn.clicked.connect(self.SnapFunc)
        self.CropBtn.clicked.connect(self.crop)
        self.AddBtn.clicked.connect(self.AddFunc)
        self.RemBtn.clicked.connect(self.RemFunc)
        self.LoadEBtn.clicked.connect(self.LoadEFunc)
        self.SaveEBtn.clicked.connect(self.SaveEFunc)
        self.RunBtn.clicked.connect(self.RunFunc)
        self.AbortBtn.clicked.connect(self.AbortFunc)
        #self.SaveBtn.clicked.connect(self.SaveFunc)
        self.histoBtn.clicked.connect(self.Histo)
        
      
        #ComboBoxes
        self.binBox.addItem("1x1","1x1")
        self.binBox.addItem("2x2","2x2")
        self.binBox.addItem("4x4","4x4")
        self.binBox.addItem("8x8","8x8")
        self.bitBox.addItem("12-bit (high well capacity)","12-bit (high well capacity)")
        self.bitBox.addItem("12-bit (low noise)","12-bit (low noise)")
        self.bitBox.addItem("16-bit (low noise & high well capacity)","16-bit (low noise & high well capacity)")
        self.binBox.setCurrentText(binn)
        self.bitBox.setCurrentText(bit)
        self.binBox.currentIndexChanged.connect(self.binCh)
        self.bitBox.currentIndexChanged.connect(self.bitCh)
        
        #sliders
        self.expSlider.setMinimum(expMin*div)
        self.expSlider.setMaximum(expMax*div)
        self.expSlider.setValue(exp*div)  
        self.expSlider.valueChanged.connect(self.expSliderFunc)
        
        #spinbox
        self.C_expSb.setMaximum(expMax)
        self.C_expSb.setValue(exp)
        self.C_expSb.valueChanged.connect(self.expSbFunc)
        self.C_expSb.setSingleStep(float(step))
        
        self.E_expSb.setMaximum(expMax)
        self.E_expSb.setValue(exp)
        self.E_expSb.valueChanged.connect(self.expSbFunc)
        self.E_expSb.setSingleStep(float(step))
        self.E_expSb.setValue(exp)
        self.E_expSb.valueChanged.connect(self.expSbFunc)
        self.repeat.setValue(1)
        self.led.setValue(2)
        self.rec.setValue(0)

        
        self.dur.setSingleStep(float(step))  
        
        self.Green.stateChanged.connect(self.green)
        self.Red.stateChanged.connect(self.red)
        
        self.Valve1.stateChanged.connect(self.valve1)
        self.Valve2.stateChanged.connect(self.valve2)
        
        self.progressBar.setValue(0)
        self.path.setText("default")
        
    
    '''TAB1: Control'''
    def LiveFunc(self):
        cv2.namedWindow('Video')
        mmc.startContinuousSequenceAcquisition(1)
        while True:
                g = mmc.getLastImage()
                if mmc.getRemainingImageCount() > 0:
                    g = mmc.getLastImage()
                    cv2.imshow('Video', g)
                else:
                    print('No frame')
                if cv2.waitKey(32) >= 0:
                    break
        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()
        #mmc.reset()
        
    def crop(self):

        mmc.clearROI()
        mmc.snapImage()
        img = mmc.getImage()
        crop_w_mouse(img)
        #crop_w_mouse_live(img)
        print "image width: "+str(mmc.getImageWidth())
        print "image height: "+str(mmc.getImageHeight())
      
    def Histo(self):
        print "press q to quit"

        cv2.namedWindow('Histogram', cv2.CV_WINDOW_AUTOSIZE)
        cv2.namedWindow('Video')
        
        #Set hist parameters
        hist_height = 512
        hist_width = 512
        nbins = 512
        bin_width = hist_width/nbins
        #512*2560*2160
        
        range_g=65536 #256

        #Create an empty image for the histogram
        h = np.zeros((hist_height,hist_width))
        rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint8)
        mask_red = np.ones((mmc.getImageHeight(),mmc.getImageWidth()),dtype=np.uint8) * 255
        mask = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint8)
        mask[:,:,2] = mask_red[:,:] #red mask (0,0,256) (r,g,b)

        
        mmc.startContinuousSequenceAcquisition(1)
        while True:
                g = mmc.getLastImage()
                if mmc.getRemainingImageCount() > 0:
                    g = mmc.getLastImage()
                    rgb2 = cv2.cvtColor(g.astype("uint16"),cv2.COLOR_GRAY2RGB)
                    rgb2[g>thd]=mask[g>thd]*256
                    cv2.imshow('Video', rgb2)
                        
                else:
                    print('No frame')
                if cv2.waitKey(32) >= 0:
                    break
                
                
                #Calculate and normalise the histogram
                hist_g = cv2.calcHist([g],[0],None,[nbins],[0,range_g])
                cv2.normalize(hist_g,hist_g,hist_height,cv2.NORM_MINMAX)
                hist=np.uint16(np.around(hist_g))
        
                #Loop through each bin and plot the rectangle in white
                for x,y in enumerate(hist):
                    cv2.rectangle(h,(x*bin_width,y),(x*bin_width + bin_width-1,hist_height),(255),-1)
        
                #Flip upside down
                h=np.flipud(h)
        
                #Show the histogram
                cv2.imshow('Histogram',h)
                h = np.zeros((hist_height,hist_width))
                #rgb = np.zeros((mmc.getImageHeight(),mmc.getImageWidth(),3),dtype=np.uint16)
          
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key is pressed, break from the loop
                if key == ord("q"):
                    break

        cv2.destroyAllWindows()
        mmc.stopSequenceAcquisition()

    def SnapFunc(self):
      #open snap window
      #mmc.snapImage()
      #img = mmc.getImage()
      #plt.imshow(img, cmap='gray')
      #plt.show()  # And window will appear
      #mmc.setProperty('Zyla','Overlap','Off')
      
      global curve, data
      
      app = QtGui.QApplication([])

      p = pg.plot()
      p.setWindowTitle('live plot from serial')
      curve = p.plot()

      data = [0]
      
      timer = QtCore.QTimer()
      timer.timeout.connect(update)
      timer.start(0)
      
      print "snap"
      
    def expSliderFunc(self,expp):
      global exp
      exp=expp/float(div)
      print "wanted exp: "+str(exp)
      #print "actual exp: "+mmc.getProperty('Zyla', 'Exposure')
      self.C_expSb.setValue(expp/float(div))
      self.E_expSb.setValue(expp/float(div))
      mmc.setProperty(DEVICE[0], 'Exposure', exp)
      print "actual exp: "+mmc.getProperty('Zyla', 'Exposure')
      
    def binCh(self,i):
        global binn
        binn = self.binBox.currentText()
        mmc.setProperty('Zyla', 'Binning', str(binn))
        print "Binning set at", mmc.getProperty('Zyla','Binning') 

    def bitCh(self):
        global bit
        bit = self.bitBox.currentText()
        mmc.setProperty('Zyla', 'Sensitivity/DynamicRange', str(bit))
        print "Bit depth set at", mmc.getProperty('Zyla','Sensitivity/DynamicRange') 
        

      
    def expSbFunc(self,expp):
      global exp
      exp=expp
      self.expSlider.setValue(expp*div) 
      
      
    def green(self,toggle_g):
      if toggle_g:
          print "green ON"
          self.led.setValue(1)
          device.setFIOState(green_lj, 1)
      else :
          print "green OFF"
          device.setFIOState(green_lj, 0)
          
    def red(self,toggle_r):
      if toggle_r:
          print "red ON"
          self.led.setValue(2)
          device.setFIOState(red_lj, 1)
      else :
          print "red OFF"
          device.setFIOState(red_lj, 0)
          
          
          
    def valve1(self,toggle_v1):
      
      if toggle_v1:
          print "valve1 ON"
          #device.setFIOState(v1_lj, 1)
          DAC0_VALUE = device.voltageToDACBits(5.5, dacNumber = 0, is16Bits = False)
          device.getFeedback(u3.DAC0_8(DAC0_VALUE))        # Set DAC0 to 5 V
          if self.Valve2.isChecked() : #if valve2 activated
              self.odo.setValue(2) #odor 2
              print "odor: 2"
          else :
              self.odo.setValue(1) #odor 1
              print "odor: 1"


      else :
          print "valve1 OFF"
          print "odor: 0"
          self.odo.setValue(0) #no odors: odor 0
          DAC0_VALUE = device.voltageToDACBits(0, dacNumber = 0, is16Bits = False)
          device.getFeedback(u3.DAC0_8(DAC0_VALUE))        # Set DAC0 to 5 V
          
          
          
    def valve2(self,toggle_v2):
        
      if toggle_v2:
          print "valve2 ON"
          #device.setFIOState(v2_lj, 1)
          DAC1_VALUE = device.voltageToDACBits(5.5, dacNumber = 1, is16Bits = False)
          device.getFeedback(u3.DAC1_8(DAC1_VALUE))        # Set DAC0 to 5 V
          if self.Valve1.isChecked() : #if valve1 activated
              self.odo.setValue(2) #odor 2
              print "odor: 2"
          else :
              self.odo.setValue(0) #no odor
              print "odor: 0"
      else :
          print "valve2 OFF"
          #device.setFIOState(v2_lj, 0)
          DAC1_VALUE = device.voltageToDACBits(0, dacNumber = 1, is16Bits = False)
          device.getFeedback(u3.DAC1_8(DAC1_VALUE))        # Set DAC0 to 5 V
          if self.Valve1.isChecked() : #if valve2 activated
              self.odo.setValue(1) #odor 2
              print "odor: 1"
          else :
              self.odo.setValue(0) #no odor
              print "odor: 0"
          self.odo.setValue(1) #odor 1
    
        
        
    '''TAB2: Epochs and run'''
    def AddFunc(self):
        print "added element in row "+str(self.listE.currentRow()+1)
        global epoch_seq
        global exp
        name = self.name.text()
        dur = self.dur.value()
        odo = self.odo.value()
        led = self.led.value()
        rec = self.rec.value()
        #epoch_seq.append([name,exp,led,odo,dur,rec])
        epoch_seq.insert(self.listE.currentRow()+1,[name,exp,led,odo,dur,rec]) #add in list
        self.listE.insertItem(self.listE.currentRow()+1,name + ", e:" +str(exp)+", l:"+str(led)+", o:" +str(odo) +", d:"+str(dur) + " s, noRecord: "+str(rec))
        #add in gui

        
    def RemFunc(self):
        print "removed element in row "+str(self.listE.currentRow())
        global epoch_seq
        print epoch_seq
        print len(epoch_seq)
        self.listE.takeItem(self.listE.currentRow()) #remove in gui
        epoch_seq.pop(self.listE.currentRow()) #remove in list

        
        
        
    def LoadEFunc(self):
      global epoch_seq
      print "select file to load"
      root = Tkinter.Tk()
      root.withdraw()
      currdir = "E:/OIIS epoch"
      filepath = tkFileDialog.askopenfilename(initialdir=currdir, title='select epoch list')
      with open(filepath, "rb") as fp:   # Unpickling
              epoch_seq = pickle.load(fp)
      for i in range(len(epoch_seq)):
              self.listE.addItem(epoch_seq[i][0] + ", e:" +str(epoch_seq[i][1])+", l:"+str(epoch_seq[i][2])+", o:" +str(epoch_seq[i][3]) +", d:"+str(epoch_seq[i][4]) + " s, noRecord: "+str(epoch_seq[i][5]))
      print "epochs loaded"
      filepath.close()
      
      
    def SaveEFunc(self):
      global epoch_seq
      root = Tkinter.Tk()
      root.withdraw()
      print "select filepath to save"
      currdir = "E:/OIIS epoch"
      filepath = tkFileDialog.asksaveasfilename(defaultextension=".p", initialdir=currdir, title='select savefile')
      with open(filepath, "wb") as fp:   #Pickling
              pickle.dump(epoch_seq, fp)
      print "epochs saved"
      
      #running epochs
    def RunFunc(self):
#        cv2.destroyAllWindows()
#        mmc.stopSequenceAcquisition()
        print "start run"
        rep=self.repeat.value()
        runEpoch(mmc,device,rep)
        print "end run"
      
      
    def AbortFunc(self):
      
      
      
      #stop odor
      device.setFIOState(v1_lj, 0)
      #stop led
      device.setFIOState(green_lj, 0)
      device.setFIOState(red_lj, 0)
      #abort video
      cv2.destroyAllWindows()
      mmc.stopSequenceAcquisition()
      #mmc.reset()
      print "aborted"
      

    
    '''TAB3: Save'''
    def SaveFunc(self):
      global frames, epoch_seq, timestamps, meta
      namep=self.path.text()
      framesnp=np.asarray(frames)
      saveAsMultipageTif(framesnp,savepath,namep,meta,k=512)
      print "tiff saved!!"
      np.save(savepath+"/"+namep+"/numpy.npy",framesnp)
      print "npy saved!!"
      with open(savepath+"/"+namep+"/epoch.p", "wb") as fp:   #Pickling
              pickle.dump(epoch_seq, fp)
      with open(savepath+"/"+namep+"/comment.p", "wb") as fpp:   #Pickling
              pickle.dump(self.comment.toPlainText(), fpp)
      with open(savepath+"/"+namep+"/timestamps.p", "wb") as fppp:   #Pickling
              pickle.dump(timestamps, fppp)
      with open(savepath+"/"+namep+"/meta.p", "wb") as fppp:   #Pickling
              pickle.dump(meta, fppp)
      print "add. info saved"
      


      
      
      
      
    '''Other'''
    def closeEvent(self, event):   # to clean up, closes labjack and windows
      #global device
      self.win.close()
      device.setFIOState(green_lj, 0)
      device.setFIOState(red_lj, 0)
      #device.setFIOState(v1_lj, 0)
      #device.setFIOState(v2_lj, 0)
      DAC0_VALUE = device.voltageToDACBits(0, dacNumber = 0, is16Bits = False)
      device.getFeedback(u3.DAC0_8(DAC0_VALUE))        
      DAC1_VALUE = device.voltageToDACBits(0, dacNumber = 1, is16Bits = False)
      device.getFeedback(u3.DAC1_8(DAC1_VALUE))   
      device.close()
      
      print "closing device"
      ser.close() #arduino serial
      mmc.unloadAllDevices() 
            
      event.accept()   
      
            


##Launching everything
if __name__ == '__main__':
    
    """labjack init"""
    try:
        device = u3.U3() #Open first found U3
    except:
        #Handle all exceptions here
        print "open error" # TO FIX : adapt error msg
    """MicroManager Init"""

    mmc = MMCorePy.CMMCore()
    mmc.loadDevice(*DEVICE)
    mmc.initializeAllDevices()
    mmc.setCameraDevice(DEVICE[0])
    
    """trigger mode"""
    #mmc.
    
    """initial camera properties"""
    mmc.setProperty('Zyla', 'Binning', binn)
    print "Binning set at", mmc.getProperty('Zyla','Binning')  
    mmc.setProperty('Zyla', 'Exposure', exp)
    mmc.setProperty('Zyla', 'AcquisitionWindow', AcqWindow)
    mmc.setProperty('Zyla', 'PixelReadoutRate', PixRR)
    mmc.setProperty('Zyla', 'Sensitivity/DynamicRange', bit)
    mmc.setProperty('Zyla','ElectronicShutteringMode','Global') #Rolling Global
    mmc.setProperty('Zyla','Overlap','Off')
    

    print mmc.getProperty('Zyla', 'Sensitivity/DynamicRange')
    print mmc.getProperty('Zyla','ElectronicShutteringMode')
    
    
    
 
    print "exp: " + str(exp)+" min: "+str(expMin)+" max: "+str(expMax)
    exp=float(mmc.getProperty(DEVICE[0], 'Exposure'))
    expMin=float(mmc.getPropertyLowerLimit(DEVICE[0], 'Exposure'))
    #expMax=float(mmc.getPropertyUpperLimit(DEVICE[0], 'Exposure'))
    print "exp: " + str(exp)+" "+str(expMin)+" "+str(expMax)
    
    print "image width: "+str(mmc.getImageWidth())
    print "image height: "+str(mmc.getImageHeight())
    

    


    #Launch GUI
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow() 
    window.show()
    sys.exit(app.exec_())
    
