import numpy as np
from slap2_utils.utils.roi_utils import roiImg, roiBoolean, roiLabels

class DummyROI:
    def __init__(self, shapeData, z):
        self.shapeData = shapeData
        self.z = z

class DummyMetaData:
    def __init__(self, rois):
        class AcquisitionContainer:
            def __init__(self, rois):
                self.ROIs = rois
        self.AcquisitionContainer = AcquisitionContainer(rois)

class DummyDataFile:
    def __init__(self):
        self.header = {
            'dmdPixelsPerRow': 5,
            'dmdPixelsPerColumn': 5
        }
        shapeData = (np.array([1, 2, 3]), np.array([1, 2, 3]))
        self.metaData = DummyMetaData([DummyROI(shapeData, 10)])
        self.fastZs = [10]

def test_roiImg():
    df = DummyDataFile()
    img = roiImg(df, 0)
    assert img.shape == (5, 5)
    assert np.sum(img) == 3
    assert img[0, 0] == 1
    assert img[1, 1] == 1
    assert img[2, 2] == 1

def test_roiBoolean():
    df = DummyDataFile()
    boolean_img = roiBoolean(df, 0)
    assert boolean_img.shape == (5, 5)
    assert boolean_img.dtype == bool
    assert np.sum(boolean_img) == 3
    assert boolean_img[0, 0]
    assert boolean_img[1, 1]
    assert boolean_img[2, 2]

def test_roiLabels_without_refstack():
    df = DummyDataFile()
    labels = roiLabels(df)
    assert labels.shape == (1, 5, 5)
    assert np.sum(labels == 1) == 3
    assert labels[0, 0, 0] == 1
    assert labels[0, 1, 1] == 1
    assert labels[0, 2, 2] == 1
