import numpy as np
from .trace_pixel import TracePixel
import copy



class Trace:
    def __init__(self, dataFile, zIdx=0, chIdx=0):
        self.dataFile = dataFile
        self.zIdx = zIdx
        self.chIdx = chIdx
        self.TracePixels = []
        self.pixelIdxs = []

    @property
    def superPixelIds(self):
        return [pixel.superPixelId for pixel in self.TracePixels]

    def setPixelIdxs(self, rasterPixels=None, integrationPixels=None):
        if isinstance(rasterPixels, np.ndarray) and np.issubdtype(rasterPixels.dtype, np.bool_):
            rasterPixels = self.checkMapDims(rasterPixels)
            temp_=np.full(int(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn']), 1)
            i=0
            while i<(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn']):
                temp_[i]=temp_[i]*(i+1)
                i=i+1

            rasterPixels = temp_

        if isinstance(integrationPixels, np.ndarray) and np.issubdtype(integrationPixels.dtype, np.bool_):
            integrationPixels = self.checkMapDims(integrationPixels)
            temp2=np.full(int(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn']), 1)
            i=0
            while i<(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn']):
                temp2[i]=temp2[i]*(i+1)+self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn']
                i=i+1
            integrationPixels = temp2


        pixelIdxs_ = np.uint32(np.concatenate((rasterPixels, integrationPixels), axis=None))
        self.TracePixels = self.getTracePixels(pixelIdxs_)
        self.pixelIdxs = pixelIdxs_

    def checkMapDims(self, map_):
        dmdPixelsPerRow = self.dataFile.header['dmdPixelsPerRow']
        dmdPixelsPerColumn = self.dataFile.header['dmdPixelsPerColumn']

        print(map_.shape, (dmdPixelsPerRow, dmdPixelsPerColumn))
    
        if dmdPixelsPerColumn != dmdPixelsPerRow and map_.shape == (dmdPixelsPerColumn, dmdPixelsPerRow):
            map_ = map_.T

        assert map_.shape == (dmdPixelsPerRow, dmdPixelsPerColumn), \
            f"Incorrect map size. Map needs to be size [{dmdPixelsPerRow},{dmdPixelsPerColumn}]"
        return map_

    def loadData(self):
        # probably unneeded. Trace Pixels load on process.
        self.TracePixels = self.TracePixels.load()

    def process(self, windowWidth_lines, expectedWindowWidth_lines):
        for i in self.TracePixels:
            i.load()

        print(self.TracePixels)

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


    def processAsync(self, windowWidth_lines, expectedWindowWidth_lines):
        hFuture_ = self.TracePixels.processAsync(windowWidth_lines, expectedWindowWidth_lines)

        def finalize(hFuture):
            self.TracePixels, trace = hFuture.fetchOutputs()

        hFuture = hFuture_.afterAll(finalize, 1, PassFuture=True)
        return hFuture

    def getTracePixels(self, pixelIdxs):
        pixelIDs = np.unique(pixelIdxs) 
        for i in range(len(pixelIDs)):
            pixelIDs[i]=pixelIDs[i]-1
        dmdNumPix = self.dataFile.header['dmdPixelsPerRow'] * self.dataFile.header['dmdPixelsPerColumn']
        
        pixelReplacementMap = self.dataFile.zPixelReplacementMaps
        


        intMask = pixelReplacementMap[1,:] >= dmdNumPix
        j=0
        for i in intMask:
            if i:
                pixelReplacementMap[0,j]=pixelReplacementMap[0,j]+dmdNumPix
            j=j+1
        sortIdxs = np.argsort(pixelReplacementMap[0])
   
       
        unique, idxs = np.unique(pixelReplacementMap[0], return_counts=True)
        validSuperPixelIDs = pixelReplacementMap[1]
        validCounts, validSuperPixelIDs = np.unique(validSuperPixelIDs, return_counts=True)

        existingSuperPixelIDs = [pixel.superPixelId for pixel in self.TracePixels]
        C, ia, ib = np.intersect1d(validSuperPixelIDs, existingSuperPixelIDs, return_indices=True)

        validSuperPixelIDs = np.delete(validSuperPixelIDs, ia)
        validCounts = np.delete(validCounts, ia)
        temp3=validSuperPixelIDs
        validSuperPixelIDs=validCounts
        validCounts=temp3
  
        ExistingTracePixels = [self.TracePixels[i] for i in ib]

        NewTracePixel = TracePixel()
        NewTracePixel.fileName = self.dataFile.filename
        NewTracePixel.bytesPerCycle = self.dataFile.header['bytesPerCycle']
        NewTracePixel.firstCycleOffsetBytes = self.dataFile.header['firstCycleOffsetBytes']
        NewTracePixel.numCycles = self.dataFile.num_cycles

        NewTracePixel.linesPerCycle = self.dataFile.header['linesPerCycle']

        
        NewTracePixels = [copy.deepcopy(NewTracePixel) for x in range(len(validSuperPixelIDs))]

      
        superPixelNumPixelsIDs, superPixelNumPixels = np.unique(pixelReplacementMap[1], return_counts=True)

      
        ia = np.where(np.isin(superPixelNumPixelsIDs, validSuperPixelIDs))[0]
        superPixelNumPixels = superPixelNumPixels[ia]
        for idx in range(len(NewTracePixels)):
            NewTracePixels[idx].superPixelId = validSuperPixelIDs[idx]
            NewTracePixels[idx].superPixelNumPixels = superPixelNumPixels[idx]

            NewTracePixels[idx].superPixelNumPixelsSelected = validCounts[idx]
  
        
        for lineIdx in range(len(self.dataFile.lineSuperPixelIDs)):
            lineZIdx = self.dataFile.lineFastZIdxs[lineIdx]
            if int(lineZIdx) != self.zIdx:
                continue
            print("1")
            lineSuperPixelIDs = self.dataFile.lineSuperPixelIDs[lineIdx]
            lineSuperPixelIDs = lineSuperPixelIDs[0]
            # left off, rest is good so far
            mask = np.isin(validSuperPixelIDs, lineSuperPixelIDs)
            positions = []
            for i in range(len(mask)):
                if mask[i]:
                    firstocc=np.where(lineSuperPixelIDs==validSuperPixelIDs[i])
                    positions.append(firstocc[0][0]+1)
                else: 
                    continue

            byteOffsets = [(x - 1) * 2 for x in positions]
            byteOffsets = [x+self.dataFile.lineDataNumElements[lineIdx] * 2 * (self.chIdx - 1) for x in byteOffsets]
            byteOffsets = [x+self.dataFile.lineDataStartIdxs[lineIdx] * 2 for x in byteOffsets]
 
            byteOffsets = [int (x-self.dataFile.header['firstCycleOffsetBytes']) for x in byteOffsets]
            pixIdxs = np.where(mask)
            pixIdxs= [int(x) for x in pixIdxs[0]]


            for x in pixIdxs:
                NewTracePixels[x].byteOffsets.append(byteOffsets[pixIdxs.index(x)])
                NewTracePixels[x].lineIdxs=lineIdx
     
            


        print(NewTracePixels[0].byteOffsets)

 
        for x in ExistingTracePixels:
            NewTracePixels.append(x)
        TracePixels=NewTracePixels
        sorted_trace_pixels = sorted(TracePixels, key=lambda x: x.superPixelId)
        return TracePixels



