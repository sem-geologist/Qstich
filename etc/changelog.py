changelog = """
# 0.1-alpha

* added code to check if scaned filenames have any BSE,AsB or BEI part, and setting one as base image. If it don't - then dialog to chose from scaned types appears to user (so if in Esprit settings it was aliased differently you have to tell that)
* tided up the project dir structure (droped UI files into ui folder, icons to icons, changelog to etc...)


# 0.1-pre-alpha

* filters implimented, making the program partily complete

--known bugs:
    -in filter tab and view when selecteting 8bit or 32 bit images the filtered image gets not generated properly (values are cut at 255 instead of geting full 16bit range)

# 0.0.3-dev

* got rid of some widgets, simplified UI. From now one boxWidget (instead of two separate widgets) is used to chose sample which tile (vector) overview and 3x3 stitching preview are changed.

# 0.0.2pre-alpha

* changed the way to recognize broken bruker file names, from now function checks if (y,x) are used once or twice in the file name (Bruker uses once if doing mappings, twice for imaging detector file names if in mapping settings 'get an image' are ticked in bruker jobs, or if doing anything else tiling --THE INCONSISTANCY of BRUKER SUCKS)

* modified functions allowing to open directory with images. (ndimage package is used from scipy)

* input can be also images, from now allowing also stitching just BSE images


--known bugs:

- stitching sometimes doesnt work with some angle corrections, the tile array size missmatches the selection of stitched array by one. The bug is being investigated.

- sometimes bruker have broken tags just with numbers:
        i.e.:
            <1> blah blah </1>
            <2> 
      as workaround for now is easier to open files and remove fucked up tags.

- some of the data after reset button are not cleared.

- the little memory leak were observed.

- pyqtgraph slows completely further processing if 'view all' is not activated at least once on the graphs


# 0.0.1alpha

* initial version.

* works just with txt input files.

* saves just tif and png"""