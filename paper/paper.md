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
    orcid: Author Without ORCID
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

Two-photon microscopy is an important technique used for deep, *in vivo*, recordings of neuronal activity from fluorscent biosensors. However, the neural acitivty frequently occurs at orders of magnetitude faster than what a typical laser-scanning two photon microscope can record. To over come this limiation several novel scanning techqiues have been developed, but these techniques result in neural data being stored in complicated file structures rather than typical image formats. We present our Python tools to interact with such a data structure generated from a novelly designed two-photon microscope, SLAP2, capable of recording neural activity at kilohertz.


# Statement of need

To overcome the inheriant speed limitations of two-photon imaging, the Scanned Line Angular Projection (SLAP) microscope was developed to make use of elements of random-access and projection microscopy to increase the aquistion rate of two-photon imaging for the recording of neuronal activity [@Kazemipour2019]. The second generation of this technology builds upon these concepts in the designs of SLAP2, a commmerically avaliable microscope kit [@mbfSLAP2]. However, the custom tools needed to read data from the binary files generated during high-speed acquistions of neural activity are not written in the Python programming language. Making it cumbersome to design worklfows that leverage packages in the Python ecosystem. To over come this limitation we developed the Python library, SLAP2 Utils. Our package provides pure Python implemenation of functions needed to read the raw microscope data. Additionally we provide tools for visualizing recorded data, processing functions, and several functions we use while running experiments.

# SLAP2 Datafile

# Visualization
Figures can be included like this:
![Caption for example figure.\label{fig:example}](docs/img/pyntIntensity.png)

Figures can be included like this:
![Caption for example figure.\label{fig:example}](docs/img/pyntLines.png)
and referenced from text using \autoref{fig:example}.



# Citations


# Acknowledgements

The development of this Python library was supported by funds from the Canadian Institutes of Health Research (CIHR) Foundation Award (FDN-148468).

# References