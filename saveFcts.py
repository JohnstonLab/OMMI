# -*- coding: utf-8 -*-
"""
Created on Fri Aug 16 13:59:59 2019

@author: Louis Vande Perre

ADD DESCRIPTION
"""
import numpy as np
from tifffile import imsave


def saveImage(mmc):
      mmc.snapImage()
      img = mmc.getImage()
      imsave('test.tif', img)