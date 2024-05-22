import numpy as np
import matplotlib.pyplot as plt
from skimage.draw import polygon_perimeter
 
from ..utils import trace

def returnAllTrace(datafile, chIdx=1,  zIdx=1, window=10, expectedWindowWidth=100):
    # Returns dictionary of traces. Key is ROI index.
    traces  = {}
    hTrace = trace.Trace(datafile, zIdx, chIdx)

    # Iterate through all ROIs in the datafile metadata
    for _roi in range(len(datafile.metaData.AcquisitionContainer.ROIs)):
        roi_shape = datafile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
        
        # Create a blank image and draw the perimeter of the ROI shape
        img = np.zeros((800, 1280), dtype=np.uint8)
        rr, cc = polygon_perimeter(roi_shape[0, :], roi_shape[1, :], shape=img.shape, clip=True)
        img[rr, cc] = 1
        
        # Create masks for the ROI
        mask = np.full((800, 1280), False, dtype=bool)
        mask[img == 1] = True
        rasterPixels = np.full((800, 1280), False, dtype=bool)
        integrationPixels = mask

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
    
    # Create a blank image and draw the perimeter of the ROI shape
    roi_shape = ROI.shapeData
    img = np.zeros((800, 1280), dtype=np.uint8)
    rr, cc = polygon_perimeter(roi_shape[0, :], roi_shape[1, :], shape=img.shape, clip=True)
    img[rr, cc] = 1
    
    # Create masks for the ROI
    mask = np.full((800, 1280), False, dtype=bool)
    mask[img == 1] = True
    rasterPixels = np.full((800, 1280), False, dtype=bool)
    integrationPixels = mask
    
    # Initialize the trace object again (redundant initialization)
    hTrace = trace.Trace(datafile, zIdx, chIdx)
    
    # Set the pixels for the trace object
    hTrace.setPixelIdxs(rasterPixels, integrationPixels)
    
    # Process the trace
    _trace1, _, _, _ = hTrace.process(1, 1)
    
    # Adjust the order of the trace
    hTrace = hTrace.orderadjust()
    
    # Plot the raw trace
    plt.plot(_trace1)
    plt.show()
    
    # Clean the volume trace
    _trace = cleanVolumeTrace(datafile, zIdx, _trace1)
    
    return _trace1, _trace
