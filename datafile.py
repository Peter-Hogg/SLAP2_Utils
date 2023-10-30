import os
import numpy as np
import mmap
import scipy.io
import h5py

#from .subclasses.metadata import MetaData
#from .utils.file_header import load_file_header_v2 -> This is relative path and it works on how you set up but I just rewrite it

import subclasses.metadata
import utils.file_header


class DataFile():

    def __init__(self, datfile):
        self.MAGIC_NUMBER = np.uint32(322379495)

        self.filename = datfile
        self.metaDataFileName = ''
        self.datFileName = ''
        self.rawData = []
        self.metaData = None
        self.StreamId = None
        self.header = None
        self.lineHeaderIdxs = None
        self._load_file()
        
        
        """#Attributes to fill in
        numCycles
        lineHeaderIdxs;
        lineDataStartIdxs;
        lineDataNumElements;
        fastZs
        lineSuperPixelIDs
        lineSuperPixelZIdxs
        lineNumSuperPixels
        zPixelReplacementMaps
        zPixelReplacementMapsNonRedundant
        lineFastZIdxs
        totalNumLines
        numChannels
        firstLineTimestamp (1,1) uint64 = 0;
        """
        
        
        
    def _load_file(self):
        base_dir, filename = os.path.split(self.filename)
        n_base = os.path.splitext(filename)[0].replace('-TRIAL', '', -1).strip()

        self.metaDataFileName = os.path.join(base_dir, n_base + '.meta')
        print(self.metaDataFileName)
        self.datFileName = os.path.join(base_dir, filename)

        if not os.path.isfile(self.metaDataFileName):
            raise FileNotFoundError('Metadata file not found.')
        self.metaData = MetaData(self.metaDataFileName)
        print('MetaData Loaded')
        
        
        if not os.path.isfile(self.datFileName):
            raise FileNotFoundError('Data file not found.')
        self.rawData = np.memmap(self.filename, dtype='uint32')
        self.header = self.load_file_header(self.rawData)
            
    # Function for loading file header:
    def load_file_header(self, rawData):
        raw_data = np.frombuffer(rawData, dtype=np.uint32)
        if raw_data.dtype != 'uint32':
            raw_data.dtype('uint32')

        file_magic_number = raw_data[0]
        assert file_magic_number == self.MAGIC_NUMBER, 'Data format error. This is not a SLAP2 data file.'
        
        
        # Currently have only implemented file version 2
        file_format_version = raw_data[1]
        assert file_format_version <= 2, 'Unknown format version'
        if file_format_version == 2:
            header = load_file_header_v2(self, raw_data)
        else:
            raise ValueError(f'Unknown file format version: {file_format_version}')

        # Load Indices
        raw_data  =  np.frombuffer(raw_data, dtype=np.uint16)
        if raw_data.dtype != 'uint16':
            raw_data.astype('uint16')

        line_idxs = np.zeros(int(header['linesPerCycle']), dtype=int)
        line_size_bytes = np.zeros(int(header['linesPerCycle']), dtype=np.uint32)
        line_idxs[0] = header['firstCycleOffsetBytes'] // 2 + 1

        line_size_bytes[0] = np.frombuffer(rawData[line_idxs[0]:line_idxs[0] + 2], dtype=np.uint32)[0]

        for idx in range(1, int(header['linesPerCycle'])):
            line_idxs[idx] = line_idxs[idx - 1] + line_size_bytes[idx - 1] // 2
            line_size_bytes[idx] = np.frombuffer(rawData[line_idxs[idx]:line_idxs[idx] + 2], dtype=np.uint32)[0]

        line_header_idxs = line_idxs
        line_data_start_idxs = line_idxs + header['lineHeaderSizeBytes'] // 2
        line_data_num_elements = (line_size_bytes - header['lineHeaderSizeBytes']) // 2


        # May need to update this conditional in the future
        if not 'referenceTimestamp' in list(header.keys()):
            header.referenceTimestamp = np.uint64(0)
            first_line_header = obj.get_line_header(1, 1)
            obj.header.referenceTimestamp = first_line_header.timestamp
        return header
