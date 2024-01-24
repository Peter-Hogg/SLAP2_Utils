import os
import numpy as np
import mmap
import scipy.io
import h5py

from .subclasses.metadata import MetaData
from .utils.file_header import load_file_header_v2

from skimage.draw import polygon_perimeter


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
        self.fastZs =  None
        self.zPixelReplacementMaps = None
        self.lineNumSuperPixels = None
        self.lineSuperPixelIDs = []
        self.lineSuperPixelZIdxs = []
        self.lineDataNumElements = []
        self.lineDataStartIdxs = []
        self.numCycles=0

        self._load_file()
        
        
        """#Attributes to fill in
        #num_cycles
        lineHeaderIdxs;
        lineDataStartIdxs;
        lineDataNumElements;
        #fastZs
        #lineSuperPixelIDs
        #lineSuperPixelZIdxs
        #lineNumSuperPixels
        #zPixelReplacementMaps
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
        self.datFileName = os.path.join(base_dir, filename)

        if not os.path.isfile(self.metaDataFileName):
            raise FileNotFoundError('Metadata file not found.')
        self.metaData = MetaData(self.metaDataFileName)
        print('MetaData Loaded')

        def load_parse_plan(self, metaData):   
            def filter_z_pixel_replacement_maps(z_maps):
                # Using list comprehension for simplified logic
                return [list(filter(lambda x: x[0] != x[1], map_)) for map_ in z_maps]

            fastz = metaData.AcquisitionContainer.ParsePlan['zs'][:]
            final_fastz = [-10203] #initiating with a value thats never found
            for i in fastz:
                final_fastz.append(i[0])

            self.fastZs = final_fastz

            print(self.fastZs)
            #Check if it breaks
            self.lineSuperPixelZIdxs = metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['sliceIdx']
            self.lineSuperPixelIDs = metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['superPixelID']
            #?
            self.zPixelReplacementMaps = metaData.AcquisitionContainer.ParsePlan['pixelReplacementMaps']
            #self.zPixelReplacementMapsNonRedundant = filter_z_pixel_replacement_maps(self.zPixelReplacementMaps)
            
            #Using list comprehension for simplified logic
            self.lineNumSuperPixels = [len(ids) for ids in self.lineSuperPixelIDs]
            self.lineFastZIdxs = np.zeros(len(self.lineSuperPixelZIdxs))
            for lineIdx in range(len(self.lineSuperPixelZIdxs)):
                lineZIdxs_=self.lineSuperPixelZIdxs[lineIdx]
           
                if len(lineZIdxs_) != 1:
                    self.lineFastZIdxs[lineIdx] = 0
                else:
                    self.lineFastZIdxs[lineIdx] = lineZIdxs_[0][0] + 1
            #?
        
        # Add additional attributes from the MetaData file
        load_parse_plan(self, self.metaData)

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
            header, self.numCycles = load_file_header_v2(self, raw_data)
        else:
            raise ValueError(f'Unknown file format version: {file_format_version}')

        # Load Indices
        raw_data  =  np.frombuffer(raw_data, dtype=np.uint16)
        if raw_data.dtype != 'uint16':
            raw_data.astype('uint16')

        line_idxs = np.zeros(int(header['linesPerCycle']), dtype=int)
        line_size_bytes = np.zeros(int(header['linesPerCycle']), dtype=np.uint32)
        line_idxs[0] = header['firstCycleOffsetBytes'] // 2 + 1
        line_size_bytes[0] = raw_data[line_idxs[0]-1]
        for idx in range(1, int(header['linesPerCycle'])):
            line_idxs[idx] = line_idxs[idx - 1] + line_size_bytes[idx - 1] // 2
            line_size_bytes[idx] = raw_data[line_idxs[idx]-1]


        line_header_idxs = line_idxs
        self.lineDataStartIdxs = line_idxs + header['lineHeaderSizeBytes'] // 2
        self.lineDataNumElements = (line_size_bytes - header['lineHeaderSizeBytes']) // 2
        self.lineDataNumElements = [int(x) for x in self.lineDataNumElements]
        self.lineDataStartIdxs = [int(x) for x in self.lineDataStartIdxs] 



        # May need to update this conditional in the future
        #if not 'referenceTimestamp' in list(header.keys()):
        #    header.referenceTimestamp = np.uint64(0)
        #    first_line_header = self.get_line_header(1, 1)
        #    self.header.referenceTimestamp = first_line_header.timestamp
        
        #first_line_header = obj.get_line_header(1, 1)
        #obj.header.referenceTimestamp = first_line_header.timestamp
        return header

    def get_line_data_idxs(self, lineIdx, cycleIdx=None):
        # Add logic to get line data indices
        pass

    def get_line_data(self, line_indices, cycle_indices, i_channel=None, async_options=None):
        if i_channel is None:
            i_channel = np.arange(1, self.header['numChannels'] + 1)
        if async_options is None:
            async_options = {
                'AsyncCallback': None,
                'AsyncLinesPerChunk': 1000
            }

        cycle_offset = (cycle_indices - 1) * self.header['bytesPerCycle']// 2
        line_start_indices = self.lineDataStartIdxs[line_indices - 1] + cycle_offset
        line_num_elements = self.lineDataNumElements[line_indices - 1]

        if self.header['channelsInterleave'] == 1:
            line_data = self.get_interleaved_data(line_start_indices, line_num_elements, i_channel)
        else:
            line_data = self.get_segmented_data(line_start_indices, line_num_elements, i_channel, async_options)

        return line_data

    def get_segmented_data(self, line_start_indices, line_num_elements, i_channel, async_options):
        channel_line_num_elements = line_num_elements // self.header['numChannels']
        channel_offsets = i_channel - 1
        line_offset_indices = min(channel_offsets) * channel_line_num_elements

        channel_range = max(channel_offsets) - min(channel_offsets) + 1
        total_line_sizes = channel_line_num_elements * channel_range
        total_line_start_indices = (line_start_indices - 1) + line_offset_indices
        line_ranges = np.column_stack((total_line_start_indices, total_line_sizes))
        num_queried_channels = len(i_channel)

        if async_options['AsyncCallback'] is None:
            # will break here. Need to replace the function of the mex file
            #line_data = MexFetchImageData('GETDATA', self.StreamId, line_ranges)
            line_data = self.get_data(self.StreamId, line_ranges)
            print(line_data)
            if num_queried_channels > 1:
                line_data = correct_segmented_channel_line(line_data, num_queried_channels)
        else:
            if num_queried_channels > 1:
                callback = lambda chunk: async_options['AsyncCallback'](correct_segmented_channel_line(chunk, num_queried_channels))
            else:
                callback = async_options['AsyncCallback']
            # will break here. Need to replace the function of the mex file   
            line_data = MexFetchImageData('GETDATAASYNC', self.StreamId, line_ranges, async_options['AsyncLinesPerChunk'], callback)

        return line_data


    def get_data(self, file_id, line_metadata):
        # Ensure rawData is in the correct dtype ('uint16') before processing
        if self.rawData.dtype != np.uint16:
            raw_data = self.rawData.view(np.uint16)
        else:
            raw_data = self.rawData

        # Process line range data
        num_lines = len(line_metadata)
        line_indices = [{'element_offset': md[0], 'num_elements': md[1]} for md in line_metadata]
        
        # Read and process data based on line_indices
        line_data = [self.read_data(raw_data, li) for li in line_indices]
        
        # Convert to desired output format (if necessary)
        output = [line for line in line_data]
        
        return output

    def read_data(self, raw_data, line_index):
        # Extract specific line data using element_offset and num_elements
        # Ensure both indices are integers
        start_index = int(line_index['element_offset'])
        end_index = int(start_index + line_index['num_elements'])
        print(start_index, end_index)
        # Ensure indexing is within bounds and adjust if necessary
        # Also ensure end_index is an integer
        end_index = min(end_index, len(raw_data))
        
        return raw_data[start_index:end_index]

