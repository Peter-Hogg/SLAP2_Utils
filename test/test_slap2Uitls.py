import os
from slap2_utils.datafile import DataFile

def test_datafile():

    test_dir = os.path.dirname(__file__)
    filename = os.path.join(test_dir, "testFile.dat")
    # Check if the file can be opened and read
    with open(filename, 'rb') as f:
        first_bytes = f.read(16)  # read the first few bytes
        print(f"First 16 bytes of the file: {first_bytes}")

    refHeader = {'firstCycleOffsetBytes': 136.0,
                 'lineHeaderSizeBytes': 40.0,
                 'laserPathIdx': 0.0,
                 'bytesPerCycle': 31270.0,
                 'linesPerCycle': 302.0,
                 'superPixelsPerCycle': 9595.0,
                 'dmdPixelsPerRow': 1280.0,
                 'dmdPixelsPerColumn': 800.0,
                 'numChannels': 1.0,
                 'channelMask': 1.0,
                 'numSlices': 28.0,
                 'channelsInterleave': 0.0,
                 'fpgaSystemClock_Hz': 200000000.0,
                 'referenceTimestamp_lower': 4015357170.0,
                 'referenceTimestamp_upper': 187.0,
                 'channels': [0],
                 'referenceTimestamp': 807174241522,
                 'file_version': 2,
                 'magic_start': 322379495,
                 'magic_end': 322379495}



    hDataFile = DataFile(filename)
    # Test if binary file is read correctly
    assert hDataFile.header == refHeader

    # Test if meta data is loaded correctly
    assert hDataFile.metaData.acqDuration_s == 10
    assert hDataFile.metaData.acqDurationCycles == 344.0
    assert hDataFile.metaData.aomActive == 0
    assert hDataFile.metaData.aomVoltage == 1.9500000000000002
    assert hDataFile.metaData.remoteFocusPosition_um == 226.75

    # Check ROIs
    assert len(hDataFile.metaData.AcquisitionContainer.ROIs) == 643
    assert hDataFile.metaData.AcquisitionContainer.ROIs[0].targetRate == 5000


def test_get_line_data():
    test_dir = os.path.dirname(__file__)
    filename = os.path.join(test_dir, "testFile.dat")
    hDataFile = DataFile(filename)
    out = hDataFile.getLineData([1, 2], [1, 2], iChannel=[1])
    
    assert isinstance(out, list)
    assert len(out) == 2  # one per line

if __name__ == '__main__':
    pytest.main()