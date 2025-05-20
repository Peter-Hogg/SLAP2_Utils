import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for testing
import matplotlib.pyplot as plt

from slap2_utils.utils.plots.slap2Plots import roiOverlay, roiOverlaySuperPix, plotPixTrace
from slap2_utils.utils.roi_utils import roiImg

class DummyROI:
    def __init__(self):
        self.shapeData = [np.array([400]), np.array([600])]
        self.z = 0

class DummyDataFile:
    header = {"dmdPixelsPerRow": 1280, "dmdPixelsPerColumn": 800}
    class Meta:
        class Container:
            ROIs = [DummyROI(), DummyROI()]
        AcquisitionContainer = Container()
    metaData = Meta()

def test_roiOverlay():
    dummy = DummyDataFile()
    refimg = np.random.rand(800, 1280)
    ax = roiOverlay(dummy, refimg, roiIdx=0, display=False)
    assert isinstance(ax, plt.Axes)

def test_roiOverlaySuperPix():
    dummy = DummyDataFile()
    refimg = np.random.rand(800, 1280)
    ax = roiOverlaySuperPix(dummy, refimg, roiIdx=0, display=False)
    assert isinstance(ax, plt.Axes)

def test_plotPixTrace():
    dffData = np.random.rand(5, 100)  # 5 pixels, 100 timepoints
    hz = 10.0
    start = 0
    end = 100
    # Patch plt.show to suppress output
    plotPixTrace(dffData, hz, start, end)
    # No assertion needed unless returning Axes; we’re verifying it runs without error
