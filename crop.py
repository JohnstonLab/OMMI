# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 12:21:37 2019

@author: Louis Vande Perre

Crop function with MM 1.4. This file contains all .py function used to crop an image.
Used in ISOI software.

TO DO :
    - Simultaneous display of crop region
"""
import cv2
import copy

global refPt
refPt = None

def crop_w_mouse(img, ROI):
    "img is open in a new window where a new ROI is set by mouse event. Return the ROI"
    global refPt
    (x,y,w,h)=ROI[-4:] #Select last elements of the vector (2 fcts called by getROI() with different returns)
    refPt = None
    print "Default ROI x "+str(x)+" y "+str(y)+" w "+str(w)+" h "+str(h)
    cv2.namedWindow('Click to crop - Esc to close')
    cv2.imshow('Click to crop - Esc to close', img)
    while(True):
        cv2.setMouseCallback('Click to crop - Esc to close',onMouse, img)
        if cv2.waitKey(33) == 27:
            break
        if cv2.getWindowProperty('Click to crop - Esc to close', 1) == -1: #Condition verified when 'X' (close) button is pressed
            break
    cv2.destroyAllWindows()
    if refPt:           #Check if refPt is not empty. If he is, ROI keep the default value
        x= refPt[0][0]
        y= refPt[0][1]
        w= refPt[1][0] - x
        h= refPt[1][1] - y
        print "selectROI x "+str(x)+" y "+str(y)+" w "+str(w)+" h "+str(h)
    return (x,y,w,h)
        
def onMouse(event, x, y, flags, params):
    #### source : https://www.pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/####
    # grab references to the global variables
    global refPt
    
    image = params
    
	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
        cv2.imshow("Click to crop - Esc to close", image)
 
	# check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
		imageCopy = copy.deepcopy(image)
        # record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		refPt.append((x, y))

		# draw a rectangle around the region of interest
		cv2.rectangle(imageCopy, refPt[0], refPt[1], (0, 255  , 0), 2)
		cv2.imshow("Click to crop - Esc to close", imageCopy)
    #print 'refPt value : ',refPt
    