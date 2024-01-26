import numpy as np
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

def cleanVolumeTrace():
    return None


def returnVolumeTrace(datafile, roiIndex, chIdx=1):
    ROI = datafile.metaData.AcquisitionContainer.ROIs[roiIndex]
    zIdx = datafile.fastz.index(ROI.z)
    roi_shape = ROI.shapeData
    img = np.zeros((800, 1280), dtype=np.uint8)
    rr, cc = polygon_perimeter(roi_shape[0,:],
                            roi_shape[1,:],

                            shape=img.shape, clip=True)

    img[rr, cc] = 1


    traces  = {}
    hTrace = Trace(exp1,zIdx,chIdx)

   
    for _roi in range(len(exp1.metaData.AcquisitionContainer.ROIs)):
        
        roi_shape = exp1.metaData.AcquisitionContainer.ROIs[_roi].shapeData;

        img = np.zeros((800, 1280), dtype=np.uint8)

        rr, cc = polygon_perimeter(roi_shape[0,:],
                                roi_shape[1,:],

                                shape=img.shape, clip=True)

        img[rr, cc] = 1
        mask = np.full((800, 1280), False, dtype=bool)
        #mask[img==1] = True
        mask[img==1]=True
        rasterPixels = np.full((800, 1280), False, dtype=bool)
        integrationPixels = mask

        dataIndex = []
        for _idx _sliceIdx in enumerate(acqParsePlan['sliceIdx']):
            if zId in _sliceIDx:
                dataIndex.append(_idx)

        trace_group=[]
        for traceIDx in range(0, _trace.shape[0], len(acqParsePlan['sliceIdx']):
            for _idx in dataIndex:
                trace_group.append([_trace[traceIDx + _idx]])



        hTrace.setPixelIdxs(rasterPixels,integrationPixels)
        # windowWidth_lines and  expectedWindowWidth_lines set to 1
        _trace, _, _, _ = hTrace.process(1,1)
        traces[_roi] = _trace
        