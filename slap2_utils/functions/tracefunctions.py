import numpy as np
import matplotlib.pyplot as plt
from skimage.draw import polygon_perimeter
 
from ..utils import trace

def returnAllTrace(datafile, chIdx=1,  zIdx=1, window=10, expectedWindowWidth=100):
    # Returns dictionary of traces. key is ROI index 
    traces  = {}
    hTrace = trace.Trace(datafile,zIdx,chIdx)

   
    for _roi in range(len(datafile.metaData.AcquisitionContainer.ROIs)):
        roi_shape = datafile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
        img = np.zeros((800, 1280), dtype=np.uint8)
        rr, cc = polygon_perimeter(roi_shape[0,:],
                                roi_shape[1,:],
                                shape=img.shape, clip=True)

        img[rr, cc] = 1
        mask = np.full((800, 1280), False, dtype=bool)
        mask[img==1]=True
        rasterPixels = np.full((800, 1280), False, dtype=bool)
        integrationPixels = mask

        hTrace.setPixelIdxs(rasterPixels,integrationPixels)
        _trace, _, _, _ = hTrace.process(window, expectedWindowWidth)
        traces[_roi] = _trace
    return traces

def cleanVolumeTrace(datafile, zId, rawTrace):
    sliceIdx = datafile.metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['sliceIdx']
    dataIndex = []
    # Need to subtract one for python indexing?
    zId -= 1
    for _idx, _sliceIdx in enumerate(sliceIdx):
        if _sliceIdx.shape[0] ==1:
            if zId in _sliceIdx:
                dataIndex.append(_idx)
    print(dataIndex)

    cleanTrace = []

    for x in range(0, rawTrace.shape[0], len(sliceIdx)):
        traceIdx = np.array(dataIndex)+x
        cleanTrace.append(np.mean(rawTrace[np.array(dataIndex)+x]))
    return np.array(cleanTrace)


def returnVolumeTrace(datafile, roiIndex, chIdx=1):
    ROI = datafile.metaData.AcquisitionContainer.ROIs[roiIndex]   
    zIdx = datafile.fastZs.index(ROI.z)
    hTrace = trace.Trace(datafile ,zIdx, chIdx)
    roi_shape = ROI.shapeData
    img = np.zeros((800, 1280), dtype=np.uint8)
    rr, cc = polygon_perimeter(roi_shape[0,:],
                            roi_shape[1,:],

                            shape=img.shape, clip=True)

    img[rr, cc] = 1
    mask = np.full((800, 1280), False, dtype=bool)
    mask[img==1]=True
    rasterPixels = np.full((800, 1280), False, dtype=bool)
    integrationPixels = mask
    hTrace = trace.Trace(datafile,zIdx,chIdx)

    hTrace.setPixelIdxs(rasterPixels,integrationPixels)
    _trace1, _, _, _ = hTrace.process(1, 1)
    plt.plot(_trace1)
    plt.show()
    _trace = cleanVolumeTrace(datafile, zIdx, _trace1)
    return _trace1, _trace
   
