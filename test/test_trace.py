import os
import numpy as np

from slap2_utils.utils.trace import Trace
from slap2_utils.utils.trace_pixel import TracePixel
from slap2_utils.functions.tracefunctions import returnAllTrace, cleanVolumeTrace, superPixelTraces
from slap2_utils.datafile import DataFile

class DummyDataFile:
    def __init__(self):
        self.header = {
            'dmdPixelsPerRow': 4,
            'dmdPixelsPerColumn': 4,
            'linesPerCycle': 1,
            'bytesPerCycle': 2,
            'firstCycleOffsetBytes': 0,
        }
        self.zPixelReplacementMaps = [np.array([[0, 1], [1, 2]])]
        self.lineSuperPixelIDs = [[np.array([1])]]
        self.lineFastZIdxs = [0]
        self.lineDataStartIdxs = [0]
        self.filename = "dummy"
        self.numCycles = 1

def test_trace_basic():
    dummy = DummyDataFile()
    trace = Trace(dummy, zIdx=0, chIdx=0)
    assert isinstance(trace, Trace)
    assert trace.zIdx == 0
    assert trace.chIdx == 0



def test_trace_gen():
    test_dir = os.path.dirname(__file__)
    filename = os.path.join(test_dir, "testFile.dat")

    if not os.path.exists(filename):
        pytest.skip("testFile.dat not found in test directory")

    datafile = DataFile(filename)
    allTraces = returnAllTrace(datafile)

    assert isinstance(allTraces, dict)
    assert len(allTraces) > 0

    # Check values
    for key, trace in allTraces.items():
        assert isinstance(key, int) or isinstance(key, str)  # ROI ID
        assert isinstance(trace, np.ndarray)
        assert trace.ndim == 1  # Assuming it's a 1D calcium/voltage trace
        assert trace.size > 0


def test_returnAllTrace_structure():
    test_dir = os.path.dirname(__file__)
    filename = os.path.join(test_dir, "testFile.dat")
    if not os.path.exists(filename):
        pytest.skip("testFile.dat not found")

    datafile = DataFile(filename)
    traces = returnAllTrace(datafile)

    assert isinstance(traces, dict)
    assert all(isinstance(k, int) for k in traces)
    assert all(isinstance(v, (np.ndarray, list)) for v in traces.values())
    assert all(v.ndim == 1 for v in traces.values())


def test_trace_set_and_order():
    dummy = DummyDataFile()
    dummy.header['dmdPixelsPerRow'] = 4
    dummy.header['dmdPixelsPerColumn'] = 4

    trace_obj = Trace(dummy, zIdx=0, chIdx=0)

    integrationPixels = np.zeros((4, 4), dtype=bool)
    integrationPixels[1, 1] = True

    trace_obj.setPixelIdxs(None, integrationPixels)

    ids = trace_obj.superPixelIds
    assert isinstance(ids, list)

    trace_obj.orderadjust()
    assert all(hasattr(pix, "y") for pix in trace_obj.TracePixels)


def test_clean_volume_trace(monkeypatch):
    class FakeROI:
        def __init__(self, z):
            self.z = z
            self.shapeData = [np.array([1]), np.array([1])]

    class DummyMetadata:
        def __init__(self):
            self.AcquisitionContainer = type("DummyAC", (), {})()
            self.AcquisitionContainer.ParsePlan = {
                "acqParsePlan": {"sliceIdx": [np.array([0]), np.array([1]), np.array([0])]}
            }
            self.AcquisitionContainer.ROIs = [FakeROI(z=201)]

    dummy = DummyDataFile()
    dummy.metaData = DummyMetadata()

    rawTrace = np.array([1.0, 2.0, 3.0])
    cleaned = cleanVolumeTrace(dummy, zId=1, rawTrace=rawTrace)
    assert isinstance(cleaned, np.ndarray)
    assert cleaned.ndim == 1


def test_superpixel_traces():
    test_dir = os.path.dirname(__file__)
    filename = os.path.join(test_dir, "testFile.dat")
    if not os.path.exists(filename):
        pytest.skip("testFile.dat not found")

    datafile = DataFile(filename)
    traces = superPixelTraces(datafile, roiIdx=0, zIdx=1, chIdx=1)

    assert isinstance(traces, np.ndarray)
    assert traces.ndim == 2
    assert traces.shape[1] > 0
