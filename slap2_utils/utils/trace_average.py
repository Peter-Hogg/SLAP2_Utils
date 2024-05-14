def returnPixTrace(datafile, roiIdx, zIdx=1, chIdx=1):
    traceObject = Trace(hDataFile,zIdx,chIdx)
 
    integrationPixels = roi_utils.roiBoolean(datafile, roiIdx)
    rasterPixels      = np.full(integrationPixels.shape, False)
    traceObject.setPixelIdxs(rasterPixels, integrationPixels)
    for pix in traceObject.TracePixels:
        pix.load()

    _pixSignal = np.zeros((traceObject.TracePixels[0].data[0].shape[0]*len(traceObject.TracePixels[0].data), len(traceObject.TracePixels)))
    for colIdx, pix in enumerate(traceObject.TracePixels):
        _pixSignal[:, colIdx] = np.array(pix.data).flatten('F')
    
    return _pixSignal