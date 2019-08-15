# -*- coding: utf-8 -*-
"""
Created on Thu Aug 15 12:21:37 2019

@author: Louis Vande Perre

Crop function with MM 1.4. This file contains all .py function used to crop an image.
Used in ISOI software.
"""
import cv2

boxes = [] #TO FIX : limit the global vars
down = False
refPt = []
cropping = False

def crop_w_mouse(img):
    "img is open in a new window where a new ROI is set by mouse event. Return the ROI"
    print "crop"
    #down = False
    global image #TO FIX : give img in argument to onMouse fct
    image = img
    while(1):
        cv2.namedWindow('real image')
        cv2.setMouseCallback('real image',onMouse, 0)
        cv2.imshow('real image', img)
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
		cropping = True
 
	# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
		# record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		refPt.append((x, y))
		cropping = False
 
		# draw a rectangle around the region of interest
		cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
		cv2.imshow("image", image)

#    if event == cv2.CV_EVENT_LBUTTONDOWN:
#         down=True
#
#         print 'Start Mouse Position: '+str(x)+', '+str(y)
#         sbox = [x, y]
#         boxes.append(sbox)
##         rect_start=(boxes[0][0],boxes[0][1])
##         rect_end=(boxes[-1][0],boxes[-1][1])
##         color=(100,255,100)
##         cv2.rectangle(img,rect_start,rect_end,color)
##         cv2.imshow("mouse",img)
#         # print count
#         # print sbox
#
#    elif event == cv2.CV_EVENT_LBUTTONUP:
#        down=False
#        print 'End Mouse Position: '+str(x)+', '+str(y)
#        ebox = [x, y]
#        boxes.append(ebox)
#        print boxes
#        crop = img[boxes[-2][1]:boxes[-1][1],boxes[-2][0]:boxes[-1][0]]
#
#        cv2.imshow('crop',crop)
#        rect_start=(boxes[-2][0],boxes[-2][1])
#        rect_end=(boxes[-1][0],boxes[-1][1])
#        color=(100,255,100)
#        cv2.rectangle(img,rect_start,rect_end,color)
#        cv2.imshow('real image',img)
#        k =  cv2.waitKey(0)
#        if ord('r')== k:
#            cv2.imwrite('Crop'+str(t)+'.jpg',crop)
#            print "Written to file"