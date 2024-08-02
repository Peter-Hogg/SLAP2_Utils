from slap2_utils.datafile import DataFile

def test_datafile():

    refHeader =     {'firstCycleOffsetBytes': 136.0,
                    'lineHeaderSizeBytes': 32.0,
                    'laserPathIdx': 0.0,
                    'bytesPerCycle': 398.0,
                    'linesPerCycle': 6.0,
                    'superPixelsPerCycle': 103.0,
                    'dmdPixelsPerRow': 1280.0,
                    'dmdPixelsPerColumn': 800.0,
                    'numChannels': 1.0,
                    'channelMask': 2.0,
                    'numSlices': 1.0,
                    'channelsInterleave': 0.0,
                    'fpgaSystemClock_Hz': 200000000.0,
                    'referenceTimestamp_lower': 649668779.0,
                    'referenceTimestamp_upper': 493.0,
                    'channels': [1],
                    'referenceTimestamp': 2118068545707,
                    'file_version': 2,
                    'magic_start': 322379495,
                    'magic_end': 322379495}



    hDataFile = DataFile('testFile.dat')
    # Test if binary file is read correctly
    assert hDataFile.header == refHeader

    # Test if meta data is loaded correctly
    assert hDataFile.metaData.acqDuration_s == 300
    assert hDataFile.metaData.acqDurationCycles == 519167.0
    assert hDataFile.metaData.acqStartTimeReference == 739194.712170625
    assert hDataFile.metaData.aomActive == 0
    assert hDataFile.metaData.aomVoltage == 5.0
    assert hDataFile.metaData.remoteFocusPosition_um == 225.0

    # Check ROIs
    assert len(hDataFile.metaData.AcquisitionContainer.ROIs) == 3 
    assert hDataFile.metaData.AcquisitionContainer.ROIs[0].targetRate == 2000



if __name__ == '__main__':
    pytest.main()