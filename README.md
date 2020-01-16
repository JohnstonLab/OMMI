# OMMI
OMMI stands for Optical Multi-Modal Imaging. This software enables low cost multi-wavelengh imaging. For example, it can be used in neuroscience to simultaneously record intrinsic signal optical imaging with fluorescence, structural, haemodynamic data. Additionally analog channels can record further data, such as respiration signals simultaneously with imaging.

The figure below shows the response map for the olfactory receptor neurons synapsing in glomeruli (IOS) and for the interneurons which are labelled with GCaMP6. The traces to the right show the response of 3 different glomeruli with the respiration signal shown below.

![figure showing OMMI in use](https://github.com/JohnstonLab/OMMI/blob/dev/Image.jpeg)

This figure shows the details of the wavelengths that can be used with appropriate filters:
![figure showing the optical spectra and filters relevant for OMMI](https://github.com/JohnstonLab/OMMI/blob/dev/OMMISpectra.png)

This software use the different packages/API :
- MicroManager-1.4 (API)
- Labjack U3 plugin
- PySerial
