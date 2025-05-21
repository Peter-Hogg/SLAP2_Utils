.. SLAP2 Utils documentation master file, created by
   sphinx-quickstart on Thu Jun  6 14:46:42 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SLAP2 Utils's documentation!
=======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


   installation
   modules/index
   viewer
   
.. toctree::
   :maxdepth: 1
   :caption: Examples

   SLAP2_Utils_example.ipynb


Overview
=======================================
The SLAP2_Utils library is designed to facilitate the reading of SLAP2 (Scanned Line Projection Microscopy version 2) binary files using Python. This utility aims to support researchers and developers working with data from SLAP2 two-photon microscopes by providing an interface to directly manipulate and analyze these files in Python as an alternative a Matlab based workflow. The SLAP2 microscope is a commerically avaliable kit from MBF bioscience (https://www.mbfbioscience.com/products/slap2).
The toolkit includes features such as:

   * Reading SLAP2 Binary Files: Convert SLAP2 proprietary binary data into accessible formats for Python.
   * Metadata Parsing: Extract and utilize metadata associated with SLAP2 data files.
   * Data Manipulation: Tools to manipulate and process data points read from the binary file.
   * Trace Extraction: Tools to extract and generate traces from ROIs imaged in integrated scan mode.
   * MatLab-based Visual Stimulus: Different kinds of visual stimulus, from checkers, moving bars, to visual stimulus utilized by the Allen Institute, ready to be imported for a SLAP2-related experiment.
   * Motion Corrections: GPU-based tools that allows calculation of motion drifts, with x, y, z changes applied directly on the ROI inside the SLAP2 software (work in progress).

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
