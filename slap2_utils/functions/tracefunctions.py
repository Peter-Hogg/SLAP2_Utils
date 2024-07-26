import numpy as np
import matplotlib.pyplot as plt
from skimage.draw import polygon_perimeter
 
from ..utils import trace
from ..utils import roi_utils
def returnAllTrace(datafile, chIdx=1,  zIdx=1, window=10, expectedWindowWidth=100):
    # Returns dictionary of traces. Key is ROI index.
    traces  = {}
    hTrace = trace.Trace(datafile, zIdx, chIdx)

    # Iterate through all ROIs in the datafile metadata
    for _roi in range(len(datafile.metaData.AcquisitionContainer.ROIs)):
 
        rasterPixels = np.full((int(datafile.header['dmdPixelsPerColumn']),
                                int(datafile.header['dmdPixelsPerRow'])),
                                False)
        integrationPixels = roi_utils.roiBoolean(datafile, _roi)

        # Set the pixels for the trace object
        hTrace.setPixelIdxs(rasterPixels, integrationPixels)
        
        # Process the trace and adjust the order
        _trace, _, _, _ = hTrace.process(window, expectedWindowWidth)
        hTrace = hTrace.orderadjust()
        
        # Store the trace in the dictionary with the ROI index as the key
        traces[_roi] = _trace
    
    return traces

def cleanVolumeTrace(datafile, zId, rawTrace):
    # Extract the slice index information from the datafile metadata
    sliceIdx = datafile.metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['sliceIdx']
    dataIndex = []
    
    # Adjust zId for Python's 0-based indexing
    zId -= 1
    
    # Find the indices of slices that match the given zId
    for _idx, _sliceIdx in enumerate(sliceIdx):
        if _sliceIdx.shape[0] == 1:
            if zId in _sliceIdx:
                dataIndex.append(_idx)

    cleanTrace = []

    # Iterate through the raw trace in steps of the number of slices
    for x in range(0, rawTrace.shape[0], len(sliceIdx)):
        traceIdx = np.array(dataIndex) + x
        # Calculate the mean of the raw trace at the relevant indices
        cleanTrace.append(np.mean(rawTrace[np.array(dataIndex) + x]))
    
    return np.array(cleanTrace)

def returnVolumeTrace(datafile, roiIndex, chIdx=1):
    # Get the ROI from the datafile metadata
    ROI = datafile.metaData.AcquisitionContainer.ROIs[roiIndex]
    
    # Find the z index corresponding to the ROI
    zIdx = datafile.fastZs.index(ROI.z)
    
    # Initialize the trace object
    hTrace = trace.Trace(datafile, zIdx, chIdx)
    
    # Create boolean arrays of raster and  integration pixels
    rasterPixels = np.full((int(datafile.header['dmdPixelsPerColumn']),
                            int(datafile.header['dmdPixelsPerRow'])),
                            False)
    integrationPixels = roi_utils.roiBoolean(datafile, roiIndex)
    
    # Initialize the trace object again (redundant initialization)
    hTrace = trace.Trace(datafile, zIdx, chIdx)
    
    # Set the pixels for the trace object
    hTrace.setPixelIdxs(rasterPixels, integrationPixels)
    
    # Process the trace
    _trace1, _, _, _ = hTrace.process(1, 1)
    
    # Adjust the order of the trace
    hTrace = hTrace.orderadjust()
    
    # Clean the volume trace
    _trace = cleanVolumeTrace(datafile, zIdx, _trace1)
    
    return _trace1, _trace



def superPixelTraces(datafile, roiIdx, zIdx=1, chIdx=1):
    """

    Args:
        datafile: SLAP2_Utils Datafile Object

        roiIdx: int 
            index value of roi in the roi list

        zIdx: Z-Plane Index

        chIdx: int
            Index of the channel being recorded

    Returns:
        _pixSignal: array
            An array of floats of a raw signal for each super pixel
    """

    traceObject = trace.Trace(datafile,zIdx,chIdx)
 
    integrationPixels = roi_utils.roiBoolean(datafile, roiIdx)
    rasterPixels      = np.full(integrationPixels.shape, False)

    traceObject.setPixelIdxs(rasterPixels, integrationPixels)
    for pix in traceObject.TracePixels:
        pix.load()

    traceObject.orderadjust()

    _pixSignal = np.zeros((traceObject.TracePixels[0].data[0].shape[0]*len(traceObject.TracePixels[0].data), len(traceObject.TracePixels)))
    for colIdx, pix in enumerate(traceObject.TracePixels):
        _pixSignal[:, colIdx] = np.array(pix.data).flatten('F')
    
    return _pixSignal