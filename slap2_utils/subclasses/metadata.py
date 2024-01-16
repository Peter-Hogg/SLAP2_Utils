# Subclasses of the primary SLAP2 Datafile
import h5py
from .slapROI import slapROI
from .acquisitionContainer import AcquisitionContainer

class MetaData():
    def __init__(self, metadatafile):
        self.metadatafile = metadatafile
        self.AcquisitionContainer = None
        self.acqDurationCycles = ''
        self.acqDuration_s = ''
        self.acqStartTimeReference= ''
        self.acquisitionPathIdx = ''
        self.acquisitionPathName = ''
        self.aomActive = ''
        self.aomVoltage = ''
        self.channelsSave = ''
        self.dmdPixelsPerColumn = ''
        self.dmdPixelsPerRow = ''
        self.enableStack = ''
        self.linePeriod_s = ''
        #machineConfiguration <HDF5 group "/machineConfiguration" (3 members)>
        self.remoteFocusPosition_um = ''
        self.samplesPerLine = ''

        with h5py.File(metadatafile, 'r') as hdf_file:
        # Read the contents of the HDF5 file into the metaData dictionary

            metaData = dict(hdf_file)
            for _key in metaData.keys():
                try:
                    metaData[_key] = hdf_file[_key][:][0][0]
                    setattr(self, _key, hdf_file[_key][:][0][0])
                except:   
                    metaData[_key] = hdf_file[_key]
                    
                
            self.AcquisitionContainer = AcquisitionContainer(self.metadatafile)