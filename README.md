# SLAP2_Utils

## Overview
The `SLAP2_Utils` library is designed to facilitate the reading of SLAP2 (Scanned Line Projection Microscopy version 2) binary files using Python. This utility aims to support researchers and developers working with data from SLAP2 two-photon microscopes by providing an interface to directly manipulate and analyze these files in Python as an alternative a Matlab based workflow. The SLAP2 microscope is a commerically avaliable kit from MBF bioscience (https://www.mbfbioscience.com/products/slap2).

## Features
- **Reading SLAP2 Binary Files**: Convert SLAP2 proprietary binary data into accessible formats for Python.
- **Metadata Parsing**: Extract and utilize metadata associated with SLAP2 data files.
- **Data Manipulation**: Tools to manipulate and process data points read from the binary file.
- **Trace Extraction**: Tools to extract and generate traces from ROIs imaged in integrated scan mode.
- **MatLab-based Visual Stimulus**: Different kinds of visual stimulus, from checkers, moving bars, to visual stimulus utilized by the Allen Institute, ready to be imported for a SLAP2-related experiment.
- **Motion Corrections**: GPU-based tools that allows calculation of motion drifts, with x, y, z changes applied directly on the ROI inside the SLAP2 software (work in progress).
  
## Technologies Used
- Python 3.x
- NumPy
- SciPy
- h5py
- scikit-image
- cupy

## Installation
Install with pip
```bash
pip install SLAP2-UTILS
```


Clone this repository

```bash
git clone https://github.com/Peter-Hogg/SLAP2_Utils.git
```
## Contributing

Contributions are welcome! If you'd like to contribute, please fork the repository and use a new branch for your contributions. Pull requests welcome. Please report bugs as we're still refining this library

## License

This project is licensed under the Mozilla Public License Version 2.0 - see the LICENSE.md file for details.

## Credits and Acknowledgements
This library was developed by Peter Hogg and Jerry Tong. It's a rework of several Matlab tools from MBF with added utility functions. Thanks to all contributors who have helped in refining this tool and helped with the project.

