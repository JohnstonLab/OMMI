# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 16:15:18 2019

@author: Louis Vande Perre
"""

import MMCorePy
import matplotlib.pyplot as plt
import cv2

mmc = MMCorePy.CMMCore()  # Instance micromanager core

# Demo camera example, connections non mandatory
mmc.loadDevice('Camera', 'DemoCamera', 'DCam')
mmc.initializeAllDevices()
mmc.setCameraDevice('Camera')

#Image capture and display
mmc.snapImage()
img = mmc.getImage()  # img - it's just numpy array
print(img)
plt.imshow(img, cmap='gray') #Seems to be better to use opencv for image displaying + VIDEO
plt.show()  # And window will appear
#We can get an image with colours
mmc.setProperty('Camera', 'PixelType', '32bitRGB')  # Change pixel type
rgb32 = mmc.getImage()
print(rgb32)