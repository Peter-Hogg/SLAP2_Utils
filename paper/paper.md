---
title: 'SLAP2 Utils: Tools for Processing SLAP2 Data'
tags:
    - Python
    - neuroscience
    - microscopy
    - calcium imaging
    - voltage imaging
authors:
  - name: Peter Hogg
    orid: 0000-0003-2176-4977
    equal-contrib: true 
    affiliation: 1

  - name: Jerry Tong
    orcid: 0009-0007-4141-556X
    equal-contrib: true
    affiliation: 1 

  - name: Kurt Haas
    orid: 0000-0003-4754-1560
    equal-contrib: false
    affiliation: 1
affiliations:
 - name: Department of Cellular and Physiological Sciences, Centre for Brain Health, School of Biomedical Engineering, University of British Columbia, Vancouver, Canada
   index: 1
date: 15 April 2024
bibliography: paper.bib
---

# Summary

Two-photon microscopy is an important technique for deep, in vivo recordings of neuronal activity from fluorescent biosensors. However, the neural activity frequently occurs at orders of magnitude faster than what a typical laser-scanning two-photon microscope can record. To overcome this limitation, several novel scanning techniques have been developed, resulting in neural data being stored in complicated file structures rather than typical image formats. The paper will mainly focus on a novelly designed two-photon microscope, SLAP2, capable of recording neural activity at kilohertz.  We present our Python toolbox with customized code that interacts with data structures generated from SLAP2 or SLAP2 software itself, providing users the ability to import the data structure into Python leverages other Python scripts and libraries.  

# Statement of need

To overcome the inherent speed limitations of two-photon imaging, the Scanned Line Angular Projection (SLAP) microscope was developed to make use of elements of random-access and projection microscopy to increase the acquisition rate of two-photon imaging for the recording of neuronal activity [@Kazemipour2019]. The second generation of this technology builds upon these concepts in the design of SLAP2, a commercially available microscope kit [@mbfSLAP2]. However, the custom tools needed to read data from the binary files generated during high-speed acquisitions of neural activity are written outside the Python programming language, making designing workflows that leverage Python ecosystem packages cumbersome. To overcome this limitation, we developed the Python library SLAP2 Utils. Our package provides pure Python implementation of functions needed to read the raw microscope data, such that SLAP2 data can be processed in the Python environment. This enables a range of Python libraries that can speed up the running of Python programs. This includes cupy, which allows scripts to be run on GPU using CUDA libraries [@cupy]. This also includes PyTorch, which has machine-learning libraries that could be applied to some programs here [@pytorch]. This Python package includes many unique features accompanying the SLAP2 microscope in a separate MATLAB UI, from motion correction on ROI to importing Python scripts, and allows quick visualization of imaged results.

# SLAP2 Datafile Pipeline

The data file pipeline provided here is a rewrite of the code provided in MBF in python, with an added function to organize the eventual parsed data (see Figure 1 \autoref{fig:fig1}) [@mbfSLAP2]. When a recording session is finished using the SLAP2 software, at least two files are usually produced: a .dat file and a .meta file. Both files contain many subfields of information. The .dat file contains mainly general information, from lines per cycle to the number of channels, and the .meta file contains more detailed information, including the parse plan of the recording and unparsed raw data (inside the memmap subfield). This means that a simple readout of the content in the files is insufficient to extract the recording properly, and additional scripts are needed to extract the data inside the memmap field correctly. The datafile.py python script imports many libraries (including numpy) and other scripts, such as fileheader.py and metadata.py, that primarily read stored data inside the two files without any processing to it yet [@numpy, @scipy, @h5py]. It outputs a datafile object after it is run with the _load_file function, which contains all the extracted information in its various fields.

In each recording, the user has the option to draw ROIs on the recording screen, such that instead of the whole point-of-view being recorded, only the responses in the ROI are recorded. Although extracting the recording with no ROI is straightforward, the user needs to extract the desired ROI information separately for a recording if an ROI is indeed present. This is necessary because there are usually multiple ROIs, and the correct ROI information must be provided in its masked array form to properly extract data from memmap. This information and the object outputted previously, are inputted into trace.py, which eventually outputs the recorded trace of the whole ROI as an object through two functions. The fields of the object need to be set up using setPixelIdxs function first. Then, the process function is called, where data is correctly parsed through in memmap and stored in the object [@numpy]. As an ROI usually contains multiple pixels, the trace.py python script also imports a script called trace_pixel.py. This script loads information about the pixels inside the trace. The output of the process function gives an average trace of the ROI, resulting from averaging values from subpixels with a convolution algorithm that fills the empty gaps created through the parse plans. The function also outputs extracted raw data inside its TracePixel subfield, but those are not spatially sorted in terms of their stored order. Here, a customized code (independent from MBF) called orderadjust can be run, such that the TracePixel is sorted with a higher index value representing trace pixels located further right than a pixel with a lower index. This allows the user to examine recorded data of higher spatial resolution as the user can now visualize recordings of values in the subpixels of an ROI instead of one value for the whole ROI.

![Figure 1: SLAP2 Pipeline. The .dat file and .meta file are inputted into datafile.py under the _load_file function, which returns a datafile object, The ROI information need to be extracted and such information are together inputted with the output of _load_file function into the trace.py, function with the order of setPixelIdxs, process, and orderadjust.\label{fig:fig1}](SLAP2_Pipeline.svg)

# SLAP2 Uility UI that Accompanies SLAP2 Software

Besides the Python script library that processes SLAP2 data, a MATLAB UI script called haasSlapUI.m has been developed to accompany the SLAP2 software. The script is written in MATLAB because some of its functionality requires the script to interact directly with the SLAP2 software, which is also written in MATLAB. Although the script is custom-written in MATLAB, the UI frequently calls on other Python scripts, such that some functionality can run much faster than if written in MATLAB. When the script is downloaded, the path must be edited to be the repository's local directory. The UI includes useful functions such as importing ROI from external sources, generating the average stack of the record (imagestacks.py python script), automatic selection of the tif file from the previous recording, and adjustment of physical shifts [@pytorch, @scikit]. The importing of the ROI and generation of the average stack is done through a simple reading of the file in Python scripts. The automatic selection of the tif file is accomplished by extracting the file name of the last time that is produced by the SLAP2 program. Lastly, The calculation of the shift adjustment is based on the phase cross correlation between the screen's point of view versus a reference stack, which is accomplished by running the xyshift_ui.py [@phasecross, @scikit]. The shift calculation is also sped up by making the GPU-based calculation, allowing the real-time shift adjustment to be conducted quickly [@cupy]. 

# Availability

All the code and scripts mentioned above are publicly available on the GitHub repository ([https://github.com/Peter-Hogg/SLAP2_Utils/tree/main]). The repository is feature-complete, and additional features are being added over time according to needs. 

# Acknowledgements

The development of this Python library was supported by funds from the Canadian Institutes of Health Research (CIHR) Foundation Award (FDN-148468). The authors also thank John Price for his valuable suggestions on the manuscript.

# Citations


# References
