import matplotlib.pyplot as plt
import numpy as np
from numpy import ndarray, dtype, floating

from SLAP2_Utils.slap2_utils.datafile import DataFile
from SLAP2_Utils.slap2_utils.subclasses.metadata import MetaData
from SLAP2_Utils.slap2_utils.utils.trace import Trace
from skimage.draw import polygon_perimeter
import os


folder = '231109_jYCaMP1_Test'
directory = os.fsencode(folder)



for file in os.listdir(directory):
    compfilename = os.fsdecode(file)
    filename, file_extension = os.path.splitext(compfilename)

    if file_extension == ".dat":
        if not os.path.exists(filename+".tif"):
            print(filename + " is being processed")
            hDataFile = DataFile(folder+'/'+compfilename)
            img = np.zeros((800, 1280), dtype=np.uint8)
            for _roi in range(len(hDataFile.metaData.AcquisitionContainer.ROIs)):

                roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
                if roi_shape.shape[0] == 2:

                    rr, cc = polygon_perimeter(roi_shape[0, :], roi_shape[1, :],

                                               shape=img.shape, clip=True)

                    img[rr, cc] = _roi + 1

            traces = {}
            noises = []
            for _roi in range(len(hDataFile.metaData.AcquisitionContainer.ROIs)):
                roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
                print(hDataFile.metaData.AcquisitionContainer.ROIs[_roi].imageMode + " mode")
                zIdx = 1;
                chIdx = 1;
                hTrace = Trace(hDataFile, zIdx, chIdx);

                #
                roi_shape = roi_shape.astype(int)
                img = np.zeros((800, 1280), dtype=np.uint8)
                for _xy in zip(roi_shape[0, :], roi_shape[1, :]):
                    img[_xy[0] - 1, _xy[1] - 1] = 1

                rasterPixels = np.full((800, 1280), False)
                integrationPixels = img.astype(np.bool_)
                hTrace.setPixelIdxs(rasterPixels, integrationPixels);
                __trace, _, _, _ = hTrace.process(10, 1000)

                x = []
                for i in range(len(__trace)):
                    x.append(i)
                noises.append((x, __trace))
                x = []
                traces[_roi] = __trace
                print(len(__trace))

                # traces[_roi]=_trace

            np.save(folder + '_train/' + filename + '_noiseonly.npy', noises)
            print(filename + " is finished being processed")
        else:
            continue

    else:
        continue
from typing import List, Tuple, Any




