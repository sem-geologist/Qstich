# Qstich

This software are designed to easy up stitching of the tiled/mosaiced SEM images/ spectral images.
At this moment sofware works just with data saved by Bruker Esprit 1.9.

# Introduction

Stitching of the tiled images can be problematic due to different kinds of abberations. Some of the SEM ahve very good measures for the problem, but some due to bad enginering introduce distortion of the left border.
While most of preinstalled SEM/EDS software have functionality of stitching images, it works often poorly, are undocumented, have very or no options, resulting in poor outcome.

# Functions
The main function of this program is to stich the images in batch manner. Additionaly this program have option to filter the often noisy spectral images with few most apropriate filters (uses opencv3 library), what is missing in most of the preinstalled SEM software.

Diferently than many kind of foto/panorama builder programs the stitching of SEM images happens explicily in 2D plane. Often the mosaicing SEM functionality allows to take images at constant x,y steps. In this program the tweeking of the stitcing parameters happens through 3x3 tiles of adjecent BSE images by tweeking rotation, and x and y resolution parameters for given sample in GUI. It is possible to "upload" many samples, tweek them and then leave the program for stitching whole stack.

Additionaly to the output images, program outputs world files useful in opening images in GIS, allowing to scale up properly in GIS programs such as QGIS (tested). The word files contains the resolution information, and will work in any metric coordinate system.
