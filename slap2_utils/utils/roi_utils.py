import numpy as np

def roiImg(datafile, idx):
    """ Returns ROI coords as a 2D array

    Args:
        datafile: SLAP2_Utils Datafile Object
            height of all peaks

        idx: int 
            index value of roi in the roi list

    Returns:
        img: array
            ints either 0 or 1 for pixels belonging to the roi
    """


    roi_shape = datafile.metaData.AcquisitionContainer.ROIs[idx].shapeData
    img = np.zeros((int(datafile.header['dmdPixelsPerColumn']),
                     int(datafile.header['dmdPixelsPerRow'])), dtype=np.uint32)
    img[roi_shape[0].astype('int'),roi_shape[1].astype('int')] = 1
    return img



def roiBoolean(datafile, idx):
    """ Returns ROI coords as a 2D array of booleans, format used in trace function

    Args:
        datafile: SLAP2_Utils Datafile Object
            height of all peaks

        idx: int 
            index value of roi in the roi list

    Returns:
        booleanPixels: array
            ints either False or True for pixels belonging to the roi
    """
    roi_shape = datafile.metaData.AcquisitionContainer.ROIs[idx].shapeData
    booleanPixels=np.full((int(datafile.header['dmdPixelsPerColumn']),
                                int(datafile.header['dmdPixelsPerRow'])),
                                False)
    booleanPixels[roi_shape[0].astype('int'),roi_shape[1].astype('int')] = True   
    
    return booleanPixels

def roiLabels(datafile, refstack=None):
    #TODO have version which uses a refrence stack 
    if refstack == None:
        roiLabels = np.zeros((len(datafile.fastZs),
                            int(datafile.header['dmdPixelsPerColumn']),
                            int(datafile.header['dmdPixelsPerRow'])))

        for lbl, roi in enumerate(datafile.metaData.AcquisitionContainer.ROIs):
            z = roi.shapeData
            plane = datafile.fastZs.index(roi.z)
            roiLabels[plane, :, :][roi.shapeData[0].astype('int'),roi.shapeData[1].astype('int')]= lbl+1
        return  roiLabels
    else:
        return
