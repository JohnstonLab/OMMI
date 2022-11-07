# OMMI - Optical Multi-Modal Imaging
This software enables low cost multi-wavelengh imaging using [cyclops LED drivers](https://open-ephys.org/cyclops) and any scientific camera compatible with µManager 2 and has a pin out signalling frame capture. Additional a [labjack[(https://labjack.com/products/u3-hv) enables simultaneous acquisition of additional signals such as respiration or other stimulus events.

An example use case is shown below: The response map for the olfactory receptor neurons synapsing in glomeruli in the olfactory bulb (measured with intrinsic signal optical imaging) and for the interneurons which are labelled with GCaMP6 ( measured with fluorescent imaging). The traces to the right show the response of 3 different glomeruli with the respiration signal shown below.

![figure showing OMMI in use](https://github.com/JohnstonLab/OMMI/blob/dev/Image.jpeg)

OMMI can be used to simultaneously record intrinsic signal optical imaging with fluorescence, structural or haemodynamic data. The figure below shows the details of the wavelengths that can be used with appropriate filters:
![figure showing the optical spectra and filters relevant for OMMI](https://github.com/JohnstonLab/OMMI/blob/dev/OMMISpectra.png)

Out of the box it is designed to work with an ANDOR sCMOS camera, it has been tested with a [zyla 5.5](https://andor.oxinst.com/products/scmos-camera-series/zyla-5-5-scmos#product-information-tabs). Modification of camInit.py will enable use of a different camera.

## Installation details:
1. Install MicroManager-2 (API) must [use a nightly build later than 2022-10-31](https://micro-manager.org/Micro-Manager_Nightly_Builds), but avoid   releases between 2022-10-25 and 2022-10-30 due to [known issues](https://github.com/micro-manager/mmCoreAndDevices/issues/288)   
2. Install the [Labjack U3 software bundle](https://labjack.com/pages/support?doc=/quickstart/u3/u3-quickstart-for-windows-overview/). 
3. Install the [arduino IDE](https://www.arduino.cc/en/software), then install the teensy boards by:  
	- To install Teensy on Arduino IDE 2.0.0, click File > Preferences.  In “Additional boards manager URLs”, copy this link: https://www.pjrc.com/teensy/package_teensy_index.json
4. Use the Arduino IDE to load the appropriate sketch onto each of your cyclops LED drivers for the red, green and blue LEDs.
5.  Install OMMI:
	1.  ‘clone or download https://github.com/JohnstonLab/OMMI.git’
	2. Change directory to OMMI folder containing environment.yml file
	3. `conda env create -f environment.yml`
	4. `conda activate OMMI`
	5. `python -m OMMI`