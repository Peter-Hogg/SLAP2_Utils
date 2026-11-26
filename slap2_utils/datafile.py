import os
import re
import numpy as np

from .subclasses.metadata import MetaData
from .utils.file_header import load_file_header_v2
from .utils.line_header import parseLineHeader


class DataFile():
    """
            A class used to load a SLAP2 binary datafile for data processing.

            Attributes
            ----------
            MAGIC_NUMBER : np.uint32
                A constant used to validate the data file.
            filename : str
                The name of the data file.
            metaDataFileName : str
                The name of the metadata file.
            datFileName : str
                The name of the data file with the '.dat' extension.
            rawData : np.memmap
                Read-only int16 memory map of the binary data file.
            metaData : MetaData
                An instance of the MetaData class to handle metadata.
            StreamId : None
                A placeholder for stream ID.
            header : dict
                Parsed file header dictionary.
            lineHeaderIdxs : np.ndarray
                One-based int16 sample indices for the start of each line header in cycle 1.
            fastZs : list or np.ndarray
                Fast Z positions for the acquisition.
            zPixelReplacementMaps : list
                Z pixel replacement maps.
            lineNumSuperPixels : list
                Number of superpixels per line.
            lineSuperPixelIDs : list
                Superpixel IDs for each line.
            lineSuperPixelZIdxs : list
                Z indices for each line's superpixels.
            lineDataNumElements : list
                Number of int16 elements in each line of data.
            lineDataStartIdxs : list
                One-based int16 start indices of each line of data in cycle 1.
            numCycles : int
                The number of complete cycles in the data file.
    """

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
        self.fastZs = None
        self.zPixelReplacementMaps = None
        self.lineNumSuperPixels = None
        self.lineSuperPixelIDs = []
        self.lineSuperPixelZIdxs = []
        self.lineDataNumElements = []
        self.lineDataStartIdxs = []
        self.numCycles = 0
        self.firstLineTimestamp = None

        self._load_file()

    def _load_file(self):
        # Loading file names and check whether file is found
        base_dir, filename = os.path.split(self.filename)
        n_base = re.sub(r'-TRIAL\d+', '', os.path.splitext(filename)[0], flags=re.IGNORECASE)
        n_base = re.sub(r'-CYCLE-?\d+', '', n_base, flags=re.IGNORECASE)

        self.metaDataFileName = os.path.join(base_dir, n_base + '.meta')
        self.datFileName = os.path.join(base_dir, filename)

        if not os.path.isfile(self.metaDataFileName):
            raise FileNotFoundError(f'Metadata file not found: {self.metaDataFileName}')
        self.metaData = MetaData(self.metaDataFileName)

        def load_parse_plan(self, metaData):
            def filter_z_pixel_replacement_maps(z_maps):
                return [list(filter(lambda x: x[0] != x[1], map_)) for map_ in z_maps]

            if not metaData.AcquisitionContainer.newFormat:
                fastz = metaData.AcquisitionContainer.ParsePlan['zs'][:]
                final_fastz = [-10203]  # initiating with a value that is never found
                for i in fastz:
                    final_fastz.append(i[0])

                self.fastZs = final_fastz

                self.lineSuperPixelZIdxs = metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['sliceIdx']
                self.lineSuperPixelIDs = metaData.AcquisitionContainer.ParsePlan['acqParsePlan']['superPixelID']
                self.zPixelReplacementMaps = metaData.AcquisitionContainer.ParsePlan['pixelReplacementMaps']

                self.lineNumSuperPixels = [len(ids) for ids in self.lineSuperPixelIDs]
                self.lineFastZIdxs = np.zeros(len(self.lineSuperPixelZIdxs))
                for lineIdx in range(len(self.lineSuperPixelZIdxs)):
                    lineZIdxs_ = self.lineSuperPixelZIdxs[lineIdx]
                    if len(lineZIdxs_) != 1:
                        self.lineFastZIdxs[lineIdx] = 0
                    else:
                        self.lineFastZIdxs[lineIdx] = lineZIdxs_[0][0] + 1
            else:
                non_empty_zs = [
                    zs for zs in metaData.AcquisitionContainer.AcquisitionPlan['activeZs']
                    if zs.size > 0
                ]
                self.fastZs = (
                    np.unique(np.concatenate(non_empty_zs))
                    if non_empty_zs
                    else np.array([], dtype=np.uint32)
                )
                self.lineSuperPixelIDs = metaData.AcquisitionContainer.AcquisitionPlan['superPixelIDs']
                self.lineSuperPixelZIdxs = metaData.AcquisitionContainer.AcquisitionPlan['activeZs']
                self.zPixelReplacementMaps = metaData.AcquisitionContainer.AcquisitionPlan['pixelReplacementMaps']
                self.zPixelReplacementMapsNonRedudant = filter_z_pixel_replacement_maps(self.zPixelReplacementMaps)
                self.lineNumSuperPixels = [int(ids.size) for ids in self.lineSuperPixelIDs]

                self.lineFastZIdxs = np.zeros(len(self.lineSuperPixelZIdxs))
                for lineIdx in range(len(self.lineSuperPixelZIdxs)):
                    lineZIdxs_ = self.lineSuperPixelZIdxs[lineIdx]
                    if lineZIdxs_.size == 0:
                        self.lineFastZIdxs[lineIdx] = 0
                    else:
                        self.lineFastZIdxs[lineIdx] = lineZIdxs_[0]

        load_parse_plan(self, self.metaData)

        if not os.path.isfile(self.datFileName):
            raise FileNotFoundError('Data file not found.')
        self.rawData = np.memmap(self.filename, dtype='int16', mode='r')
        self.load_file_header()

    def load_file_header(self):
        nbytes = len(self.rawData) * self.rawData.itemsize
        raw_data = np.frombuffer(self.rawData, dtype=np.uint32, count=nbytes // 4)

        file_magic_number = raw_data[0]
        assert file_magic_number == self.MAGIC_NUMBER, 'Data format error. This is not a SLAP2 data file.'

        file_format_version = raw_data[1]
        assert file_format_version <= 2, 'Unknown format version'
        if file_format_version == 2:
            header, self.numCycles = load_file_header_v2(self, raw_data)
        else:
            raise ValueError(f'Unknown file format version: {file_format_version}')

        self.header = header

        raw_data_int16 = np.frombuffer(self.rawData, dtype=np.int16)

        lines_per_cycle = int(header['linesPerCycle'])
        line_idxs = np.zeros(lines_per_cycle, dtype=int)
        line_size_bytes = np.zeros(lines_per_cycle, dtype=np.uint32)
        line_idxs[0] = int(header['firstCycleOffsetBytes']) // 2 + 1
        line_size_bytes[0] = np.frombuffer(
            raw_data_int16[line_idxs[0] - 1:line_idxs[0] + 1].tobytes(), dtype=np.uint32
        )[0]

        for idx in range(1, lines_per_cycle):
            line_idxs[idx] = line_idxs[idx - 1] + line_size_bytes[idx - 1] // 2
            line_size_bytes[idx] = np.frombuffer(
                raw_data_int16[line_idxs[idx] - 1:line_idxs[idx] + 1].tobytes(), dtype=np.uint32
            )[0]

        self.lineHeaderIdxs = line_idxs
        self.lineDataStartIdxs = line_idxs + int(header['lineHeaderSizeBytes']) // 2
        self.lineDataNumElements = (line_size_bytes - int(header['lineHeaderSizeBytes'])) // 2
        self.lineDataNumElements = [int(x) for x in self.lineDataNumElements]
        self.lineDataStartIdxs = [int(x) for x in self.lineDataStartIdxs]

        if self.numCycles > 0:
            if 'referenceTimestamp' not in header:
                header['referenceTimestamp'] = np.uint64(0)
                first_line_header = self.getLineHeader(1, 1)
                header['referenceTimestamp'] = first_line_header['timestamp']

            first_line_header = self.getLineHeader(1, 1)
            self.firstLineTimestamp = first_line_header['timestamp']

        return header

    def getLineHeader(self, lineIndices, cycleIndices):
        """Get parsed line headers from the data file.

        Parameters
        ----------
        lineIndices : array_like
            Positive one-based line indices within a cycle.
        cycleIndices : array_like
            Positive one-based cycle indices. A scalar is broadcast across
            multiple line indices.

        Returns
        -------
        dict or list of dict
            One dictionary for scalar input, otherwise dictionaries in input
            order.
        """
        lineValues = np.asarray(lineIndices)
        cycleValues = np.asarray(cycleIndices)
        scalarResult = lineValues.ndim == 0 and cycleValues.ndim == 0

        lineValues = lineValues.ravel()
        cycleValues = cycleValues.ravel()
        if lineValues.size == 0 and cycleValues.size == 0:
            return []
        if cycleValues.size == 1 and lineValues.size > 1:
            cycleValues = np.full(lineValues.shape, cycleValues[0])
        if lineValues.size != cycleValues.size:
            raise ValueError("Number of cycle indices must match number of line indices")

        try:
            finite = np.all(np.isfinite(lineValues)) and np.all(np.isfinite(cycleValues))
            integral = (np.all(lineValues == np.floor(lineValues)) and
                        np.all(cycleValues == np.floor(cycleValues)))
        except TypeError as exc:
            raise ValueError("All indices must be finite integers") from exc
        if not finite or not integral:
            raise ValueError("All indices must be finite integers")

        lineValues = lineValues.astype(np.int64)
        cycleValues = cycleValues.astype(np.int64)
        if np.any(lineValues <= 0) or np.any(cycleValues <= 0):
            raise ValueError("All indices must be positive integers (Matlab indexing)")
        if np.any(lineValues > int(self.header['linesPerCycle'])):
            raise ValueError("Line indices must be <= linesPerCycle")
        if np.any(cycleValues > self.numCycles):
            raise ValueError("Cycle indices must be <= numCycles")

        headerSizeBytes = int(self.header['lineHeaderSizeBytes'])
        headerSizeElements = headerSizeBytes // self.rawData.itemsize
        bytesPerCycle = int(self.header['bytesPerCycle'])
        metaData = getattr(self, 'metaData', None)
        fpgaTimeReference = (
            getattr(metaData, 'fpgaTimeReference', None)
            if metaData is not None
            else None
        )
        headers = []
        for lineIndex, cycleIndex in zip(lineValues, cycleValues):
            start = (int(self.lineHeaderIdxs[lineIndex - 1]) - 1 +
                     (cycleIndex - 1) * bytesPerCycle // self.rawData.itemsize)
            rawHeader = self.rawData[start:start + headerSizeElements].tobytes()
            headers.append(parseLineHeader(
                rawHeader,
                fpgaSystemClock_Hz=self.header.get('fpgaSystemClock_Hz'),
                referenceTimestamp=self.header.get('referenceTimestamp'),
                fpgaTimeReference=fpgaTimeReference,
            ))

        return headers[0] if scalarResult else headers

    def getLineData(self, lineIndices, cycleIndices, iChannel=None, method="Cython"):
        """Get line data from the data file.

        Parameters
        ----------
        lineIndices : array_like
            Vector of positive integers specifying line indices (matlab indexing)
        cycleIndices : array_like
            Vector of positive integers specifying cycle indices (matlab indexing)
        iChannel : array_like, optional
            Vector of positive integers specifying channel indices (matlab indexing) (default is all channels)
        method : str, optional
            Method to use for data retrieval, either "Cython" or "Python" or "Numpy" (default is "Cython")

        Returns
        -------
        lineData : list
            Line data for the specified indices
        """
        if iChannel is None:
            iChannel = np.arange(1, self.header['numChannels'] + 1)

        lineIndices = np.asarray(lineIndices, dtype=np.int64).ravel()
        cycleIndices = np.asarray(cycleIndices, dtype=np.int64).ravel()
        iChannel = np.asarray(iChannel, dtype=np.int64).ravel()

        if not np.all(lineIndices > 0) or not np.all(cycleIndices > 0) or not np.all(iChannel > 0):
            raise ValueError("All indices must be positive integers (Matlab indexing)")

        if np.any(lineIndices > self.header['linesPerCycle']):
            raise ValueError("Line indices must be <= linesPerCycle")

        if np.any(cycleIndices > self.numCycles):
            raise ValueError("Cycle indices must be <= numCycles")
        if len(cycleIndices) != len(lineIndices):
            raise ValueError("Number of cycle indices must match number of line indices")

        if np.any(iChannel > self.header['numChannels']):
            raise ValueError("Channel indices must be <= numChannels")

        hMemmap = np.memmap(self.datFileName, dtype='int16', mode='r')

        try:
            try:
                from .fast_line_data import fast_get_line_data
                lineData = fast_get_line_data(
                    hMemmap,
                    self.lineDataNumElements,
                    self.lineDataStartIdxs,
                    int(self.header['numChannels']),
                    int(self.header['firstCycleOffsetBytes']),
                    int(self.header['bytesPerCycle']),
                    lineIndices,
                    cycleIndices,
                    iChannel
                )
            except ImportError:
                lineData = []
                for idx in range(len(lineIndices)):
                    samples_per_channel = int(self.lineDataNumElements[lineIndices[idx] - 1]) // int(self.header['numChannels'])
                    tmpData = np.empty((samples_per_channel, len(iChannel)), dtype=np.int16)
                    precomputed_offset = (
                        self.lineDataStartIdxs[lineIndices[idx] - 1]
                        + (cycleIndices[idx] - 1) * int(self.header['bytesPerCycle']) // 2
                    )
                    for ch in range(len(iChannel)):
                        offset = samples_per_channel * (iChannel[ch] - 1) + precomputed_offset - 1
                        tmpData[:, ch] = hMemmap[offset:offset + samples_per_channel]
                    lineData.append(tmpData)
        finally:
            if hasattr(hMemmap, '_mmap'):
                hMemmap._mmap.close()
            del hMemmap

        return lineData
