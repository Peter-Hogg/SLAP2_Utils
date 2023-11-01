import matplotlib.pyplot as plt
import numpy as np

from SLAP2_Utils.datafile import DataFile
from SLAP2_Utils.subclasses.metadata import MetaData
from SLAP2_Utils.utils.trace import Trace



hDataFile = DataFile('TestData/Tadpole2_20230829_183310_DMD2.dat');
roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[0].shapeData

#metaData.AcquisitionContainer.ROIs[0].shapeData
zIdx = 1;
chIdx = 1;
hTrace = Trace(hDataFile,zIdx,chIdx);


from skimage.draw import polygon_perimeter

roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[0].shapeData

img = np.zeros((800, 1280), dtype=np.uint8)

rr, cc = polygon_perimeter(roi_shape[0,:], roi_shape[1,:],

                           shape=img.shape, clip=True)

img[rr, cc] = 1

plt.imshow(img)

#rasterPixels = pixelMask;
#integrationPixels = pixelMask;

pixelMask=np.full((800, 1280), True)
rasterPixels = pixelMask;
integrationPixels = pixelMask;

hTrace.setPixelIdxs(rasterPixels, integrationPixels);
#windowWidth_lines = 10;
#expectedWindowWidth_lines = 100;
#trace = hTrace.process(windowWidth_lines,expectedWindowWidth_lines);
_trace = hTrace.process(10, 100)
plt.plot(_trace)



