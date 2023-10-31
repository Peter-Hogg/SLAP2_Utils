import os
import numpy as np
import mmap
import scipy.io
import h5py


from utils.trace_pixel import TracePixel
from utils.trace import Trace
from subclasses.metadata import MetaData
from utils.file_header import load_file_header_v2
from datafile import DataFile




x=DataFile("acquisition_20230216_130937_DMD1.dat")
x._load_file()
y=Trace(x)
z=TracePixel()
z.fileName=x.filename
z.load(x.rawData)



