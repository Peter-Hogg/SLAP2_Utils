import numpy as np
import re
import trace

class TracePixel:
    def __init__(self):
        self.fileName = ""
        self.superPixelId = 0
        self.superPixelNumPixels = 0
        self.superPixelNumPixelsSelected = 0
        self.byteOffsets = []
        self.lineIdxs = []
        self.data = None
        self.isLoaded = False
        self.firstCycleOffsetBytes = 0
        self.numCycles = 0
        self.bytesPerCycle = 0
        self.linesPerCycle = 0

    def load(self, hMemmap=None):
        allLoaded = self.isLoaded
        if allLoaded:
            return

        loadedFilename = ""

        if hMemmap is not None:
            loadedFilename = hMemmap.Filename
            hMemmap.Format = 'int16'

        fileName_ = self.fileName
        fileName_ = re.sub(r'\.meta$', '.dat', fileName_, flags=re.IGNORECASE)

        if loadedFilename != fileName_:
            hMemmap = np.memmap(fileName_, dtype='int16', mode='r')
            loadedFilename = fileName_

        cycleIdxs = np.arange(0, self.numCycles, dtype=np.uint64)
        cycleByteOffsets = self.firstCycleOffsetBytes + cycleIdxs * self.bytesPerCycle
        cycleSampleOffsets = cycleByteOffsets // 2

        sampleOffsets = np.array(self.byteOffsets, dtype=np.uint64) // 2
        sampleOffsets = sampleOffsets[:, np.newaxis] + cycleSampleOffsets
        data_ = hMemmap[sampleOffsets]
        data_[data_ == np.iinfo(np.int16).min] = 0
        self.data = data_
        self.isLoaded = True

    def process(self, windowWidth_lines, expectedWindowWidth_lines):
        self.load()

        tempKernel = np.exp(-np.abs(np.arange(-4*windowWidth_lines, 4*windowWidth_lines+1) / windowWidth_lines))
        tempKernel = tempKernel.astype('float32')

        expectedKernel = np.ones(expectedWindowWidth_lines, dtype='float32')

        if self.linesPerCycle == 0 or self.numCycles == 0:
            numLines = 0
        else:
            numLines = self.linesPerCycle * self.numCycles

        sumDataWeighted = np.zeros(numLines, dtype='float32')
        sumExpected = np.zeros(numLines, dtype='float32')
        sumExpectedWeighted = np.zeros(numLines, dtype='float32')

        lineData = np.zeros((self.linesPerCycle, self.numCycles), dtype='float32')
        sampled = np.zeros((self.linesPerCycle, self.numCycles), dtype='float32')

        lineData[self.lineIdxs, :] = self.data
        sampled[self.lineIdxs, :] = 1

        lineData = lineData.flatten()
        sampled = sampled.flatten()

        spatialWeight = self.superPixelNumPixelsSelected / self.superPixelNumPixels
        weightedData = np.convolve(lineData, tempKernel * spatialWeight, mode='same')
        tempWeights = np.convolve(sampled, tempKernel, mode='same')

        expected = np.convolve(lineData, expectedKernel, mode='same')
        expectedN = np.convolve(sampled, expectedKernel, mode='same')
        expected = expected / (expectedN + np.finfo(float).eps)

        expectedWeighted = expected * tempWeights

        sumDataWeighted += weightedData
        sumExpected += expected
        sumExpectedWeighted += expectedWeighted

        trace = sumDataWeighted / (sumExpectedWeighted + np.finfo(float).eps) * sumExpected

        return trace, sumDataWeighted, sumExpected, sumExpectedWeighted
