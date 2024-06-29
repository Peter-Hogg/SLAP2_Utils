# Subclasses of the primary SLAP2 Datafile
import h5py
from .slapROI import slapROI
from .acquisitionContainer import AcquisitionContainer

class MetaData():

     """
            A class used to load a SLAP2 binary metadata file (to be done)

            Attributes
            ----------
            
            metadatafile : h5py.file
                Readout of the metadata file in the form of a h5py.file object.
            AcquisitionContainer : AcquisitionContainer
                An instance of the AcquisitionContainer class that contains acquisition-related information
            metaDataFileName : str
                The name of the metadata file.
            datFileName : str
                The name of the data file with the '.dat' extension.
            rawData : list
                A list to store the raw data from the file.
            metaData : MetaData
                An instance of the MetaData class to handle metadata.
            StreamId : None
                A placeholder for stream ID.
            header : None
                A placeholder for the file header.
            lineHeaderIdxs : None
                A placeholder for the line header indices.
            fastZs : list
                A list to store fast Z values.
            zPixelReplacementMaps : None
                A placeholder for the Z pixel replacement maps.
            lineNumSuperPixels : None
                A placeholder for the number of super pixels per line.
            lineSuperPixelIDs : list
                A list to store super pixel IDs for each line.
            lineSuperPixelZIdxs : list
                A list to store Z indices for each line's super pixels.
            lineDataNumElements : list
                A list to store the number of elements in each line of data.
            lineDataStartIdxs : list
                A list to store the start indices of each line of data.
            numCycles : int
                The number of cycles in the data file.


                
            """
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
