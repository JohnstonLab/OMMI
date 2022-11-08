# OMMI - Optical Multi-Modal Imaging
This software enables low cost multi-wavelengh imaging using [cyclops LED drivers](https://open-ephys.org/cyclops) and any scientific camera compatible with µManager 2 that has a pin out signalling frame capture. Additionaly a [labjack](https://labjack.com/products/u3-hv) enables simultaneous acquisition of auxiliary signals such as respiration or stimulus events.

An example use case is shown below: The response map for the olfactory receptor neurons synapsing in glomeruli in the olfactory bulb (measured with intrinsic signal optical imaging) and for the interneurons which are labelled with GCaMP6 ( measured with fluorescent imaging). The traces to the right show the response of 3 different glomeruli with the respiration signal shown below.

![figure showing OMMI in use](https://github.com/JohnstonLab/OMMI/blob/dev/Image.jpeg)

OMMI can be used to simultaneously record intrinsic signal optical imaging with fluorescence, structural or haemodynamic data. The figure below shows the details of the wavelengths that can be used with appropriate filters:
![figure showing the optical spectra and filters relevant for OMMI](https://github.com/JohnstonLab/OMMI/blob/dev/OMMISpectra.png)

Out of the box it is designed to work with an ANDOR sCMOS camera, it has been tested with a [zyla 5.5](https://andor.oxinst.com/products/scmos-camera-series/zyla-5-5-scmos#product-information-tabs). Modification of camInit.py will enable use of a different camera.

## Installation details:
1. Install MicroManager-2 (API) must [use a nightly build later than 2022-10-31](https://micro-manager.org/Micro-Manager_Nightly_Builds), but avoid   releases between 2022-10-25 and 2022-10-30 due to [known issues](https://github.com/micro-manager/mmCoreAndDevices/issues/288)  
2. Install Andor Driver Pack or the driver for the camera you wish to use.
   - On the Select Destination Location dialog, click browse and choose the current Micro-Manager installation directory. Then click Yes to confirm that you do want to install to that folder.
3. Check your camera works with µManager by creating a configuration using the [Hardware Configuration Wizard[(https://micro-manager.org/Micro-Manager_Configuration_Guide). Create a configuration with just you camera and save this (you will use this file later to load you camera). 
4. Add micromanager folder to path 
5. Install the [Labjack U3 software bundle](https://labjack.com/pages/support?doc=/quickstart/u3/u3-quickstart-for-windows-overview/). 
5. Install the [arduino IDE](https://www.arduino.cc/en/software), then install the teensy boards by:  
	- To install Teensy on Arduino IDE 2.0.0, click File > Preferences.  In “Additional boards manager URLs”, copy this link: https://www.pjrc.com/teensy/package_teensy_index.json
6. Use the Arduino IDE to load the appropriate sketch onto each of your cyclops LED drivers for the red, green and blue LEDs.
7. Download or clone the OMMI repository:  https://github.com/JohnstonLab/OMMI.git
8. Modify lines 13 and 14 of 'camInit.py' to specify the paths to your µManager folder and config file (created in step 3).
9. Check the device manager to see what the teeny boards in the cyclops are called. If their name does not contain 'Teensy', you need to modify line 62 of 'ArduinoTeensy.py' so that the search string when scanning for ports contains a string that matches what your teensy are named in the device manager.
10. Install OMMI:
	2. Open an anaconda prompt and...
	2. 'cd' (Change directory) to the OMMI folder containing environment.yml file
	3. Create a new environment using `conda env create -f environment.yml`
	4. Then activate the new environment `conda activate OMMI`
	5. And finally launch OMMI with `python -m OMMI`


### Notes on camera choice
- A camera with a GPIO or accessible signal for frame firing/acquisition is necessary
- For intrinsic signal imaging selecting a camera with a high well depth best SNR and appropriate frame rates for your needs
- Consideration to the shutter type, rolling vs global. Global is required for Fourier based analysis methods, e.g. [Kalatsky, V.A. & Stryker, M.P. (2003), Neuron, 38, 529-545.](10.1016/s0896-6273(03)00286-1) 