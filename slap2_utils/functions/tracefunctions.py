from slap2.utils import trace

def returnAllTrace(datafile, roiIndex, chIdx=1,  zIdx=1, window=10, expectedWindowWidth=100):
    # Returns dictionary of traces. key is ROI index 
    traces  = {}
   
    hTrace = Trace(exp1,zIdx,chIdx)

   
    for _roi in range(len(exp1.metaData.AcquisitionContainer.ROIs)):
        
        roi_shape = exp1.metaData.AcquisitionContainer.ROIs[_roi].shapeData

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
    


def returnVolumeTrace(datafile, roiIndex, chIdx=1):
    ROI = datafile.metaData.AcquisitionContainer.ROIs[roiIndex]
    
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

        hTrace.setPixelIdxs(rasterPixels,integrationPixels)
        # windowWidth_lines and  expectedWindowWidth_lines set to 1
        _trace, _, _, _ = hTrace.process(1,1)
        traces[_roi] = _trace
        