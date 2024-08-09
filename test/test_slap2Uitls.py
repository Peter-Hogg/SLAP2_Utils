from slap2_utils.datafile import DataFile

def test_datafile():

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



    hDataFile = DataFile('testFile.dat')
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



if __name__ == '__main__':
    pytest.main()