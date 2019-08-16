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

refPt = []

def crop_w_mouse(img):
    "img is open in a new window where a new ROI is set by mouse event. Return the ROI"
    global image #TO FIX : give img in argument to onMouse fct
    image = img
    while(1):
        cv2.namedWindow('Click to crop - Esc to close')
        cv2.imshow('Click to crop - Esc to close', img)
        cv2.setMouseCallback('Click to crop - Esc to close',onMouse, 0)
        if cv2.waitKey(33) == 27:
            cv2.destroyAllWindows()
            break

            
    x= refPt[0][0]
    y= refPt[0][1]
    w= refPt[1][0] - x
    h= refPt[1][1] - y
    print "selectROI x "+str(x)+" y "+str(y)+" w "+str(w)+" h "+str(h)
    return (x,y,w,h)
        
def onMouse(event, x, y, flags, params):
    #### source : https://www.pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/####
    # grab references to the global variables
	global refPt, cropping
 
	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt = [(x, y)]
 
	# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
		# record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		refPt.append((x, y))
 
		# draw a rectangle around the region of interest
		cv2.rectangle(image, refPt[0], refPt[1], (255, 0  , 0), 2)
		cv2.imshow("Click to crop - Esc to close", image)
        