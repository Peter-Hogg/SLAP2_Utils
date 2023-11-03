import matplotlib.pyplot as plt
import numpy as np

from SLAP2_Utils.datafile import DataFile
from SLAP2_Utils.subclasses.metadata import MetaData
from SLAP2_Utils.utils.trace import Trace

from skimage.draw import polygon_perimeter

hDataFile = DataFile('TestData/Tadpole2_20230829_183310_DMD2.dat');
traces = {}
for _roi in range(len(hDataFile.metaData.AcquisitionContainer.ROIs)):
    print(_roi)
    roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
    zIdx = 1;
    chIdx = 1;
    hTrace = Trace(hDataFile,zIdx,chIdx);


    #
    roi_shape= roi_shape.astype(int)
    img = np.zeros((800, 1280), dtype=np.uint8)
    for _xy in zip(roi_shape[0,:], roi_shape[1,:]):
        img[_xy[0]-1, _xy[1]-1]=1

    #plt.imshow(img)
    #plt.show()
    rasterPixels = np.full((800, 1280), False)
    integrationPixels = img.astype(np.bool_)

    hTrace.setPixelIdxs(rasterPixels, integrationPixels);
    __trace, _, _, _ = hTrace.process(10, 100)
    plt.plot(__trace[:1000])
    plt.show()
    traces[_roi] = __trace
    #traces[_roi]=_trace

print(traces)


