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

Two-photon microscopy is an important technique for deep, *in vivo*, recordings of neuronal activity from fluorescent biosensors. However, the neural activity frequently occurs at orders of magnitude faster than what a typical laser-scanning two-photon microscope can record. To overcome this limitation, several novel scanning techniques have been developed, resulting in neural data being stored in complicated file structures rather than typical image formats. We present our Python toolbox with customized codes that interact with such a data structure generated from a novelly designed two-photon microscope, SLAP2, capable of recording neural activity at kilohertz. The ability to import the data structure in Python also enables the implementation of other python scripts and libraries. This Python package includes many different features that accompany the SLAP2 microscope, from motion correction on ROI to a separate MATLAB UI that imports Python scripts and allows quick visualization of imaged results. 


# Statement of need

To overcome the inherent speed limitations of two-photon imaging, the Scanned Line Angular Projection (SLAP) microscope was developed to make use of elements of random-access and projection microscopy to increase the acquisition rate of two-photon imaging for the recording of neuronal activity [@Kazemipour2019]. The second generation of this technology builds upon these concepts in the designs of SLAP2, a commercially available microscope kit [@mbfSLAP2]. However, the custom tools needed to read data from the binary files generated during high-speed acquisitions of neural activity in specific region of interest and are written outside the Python programming language, making designing workflows that leverage Python ecosystem packages cumbersome. To overcome this limitation, we developed the Python library, SLAP2 Utils. Our package provides pure Python implementation of functions needed to read the raw microscope data, such that SLAP2 data can be processed in the Python environment. This enables ranges of Python libraries from copy that speeds up the running of Python programs by running scripts on GPU using CUDA libraries to Keras of Tensorflow (for machine learning) to copy that speeds up the running of Python programs by using CUDA and running scripts on a GPU.

# SLAP2 Datafile Pipeline

This paper first provide a python version of the code provided in MBF, with added function to organize the eventual parsed data (see \ref{Figure1}). When a recording session is finished in the SLAP2 software, at least two files are usually produced: .dat file and .meta file. Both file contains many subfields of information. The .dat file containing mainly general information, from lines per cycle to number of channels, and .meta file contains more detailed information, including the parse plan of the recording and unparsed raw data (inside the memmap subfield) from the recording. This means that a simple reading of the code is not suffice to extract the recording properly, and additional codes are needed to correctly extract the data inside the memmap field. 

![Figure1\label{Figure1}](SLAP2_Pipeline.svg)

See figure \ref{Figure1}.

![.\label{fig:figure1}](SLAP2_Pipeline.svg)


# Visualization

Figures can be included like this:

![Caption for example figure.\label{fig:example}](SLAP2_Pipeline.svg)

and referenced from text using \autoref{fig:example}.



# Citations


# Acknowledgements

The development of this Python library was supported by funds from the Canadian Institutes of Health Research (CIHR) Foundation Award (FDN-148468).

# References
