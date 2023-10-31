import numpy as np
from .trace_pixel import TracePixel




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
            rasterPixels = np.where(rasterPixels)[0]

        if isinstance(integrationPixels, np.ndarray) and np.issubdtype(integrationPixels.dtype, np.bool_):
            integrationPixels = self.checkMapDims(integrationPixels)
            integrationPixels = np.where(integrationPixels)[0] + len(integrationPixels)

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
        self.TracePixels, trace = self.TracePixels.process(windowWidth_lines, expectedWindowWidth_lines)
        return trace

    def processAsync(self, windowWidth_lines, expectedWindowWidth_lines):
        hFuture_ = self.TracePixels.processAsync(windowWidth_lines, expectedWindowWidth_lines)

        def finalize(hFuture):
            self.TracePixels, trace = hFuture.fetchOutputs()

        hFuture = hFuture_.afterAll(finalize, 1, PassFuture=True)
        return hFuture

    def getTracePixels(self, pixelIdxs):
        pixelIDs = np.unique(pixelIdxs) - 1
        dmdNumPix = self.dataFile.header['dmdPixelsPerRow'] * self.dataFile.header['dmdPixelsPerColumn']

        pixelReplacementMap = self.dataFile.zPixelReplacementMaps[self.zIdx]
        intMask = pixelReplacementMap[:] >= dmdNumPix
        pixelReplacementMap[intMask] = pixelReplacementMap[intMask] + dmdNumPix

        sortIdxs = np.argsort(pixelReplacementMap[:])
        pixelReplacementMap = pixelReplacementMap[sortIdxs]
        idxs = np.where(np.isin(pixelIDs, pixelReplacementMap[:]))[0]
        validMask = idxs > 0

        idxs = idxs[validMask]
        validSuperPixelIDs = pixelReplacementMap[idxs]
        validCounts, validSuperPixelIDs = np.unique(validSuperPixelIDs, return_counts=True)

        existingSuperPixelIDs = [pixel.superPixelId for pixel in self.TracePixels]
        ia, ib = np.intersect1d(validSuperPixelIDs, existingSuperPixelIDs, return_indices=True)

        validSuperPixelIDs = np.delete(validSuperPixelIDs, ia)
        validCounts = np.delete(validCounts, ia)

        ExistingTracePixels = [self.TracePixels[i] for i in ib]

        NewTracePixel = TracePixel()
        NewTracePixel.fileName = self.dataFile.filename
        NewTracePixel.bytesPerCycle = self.dataFile.header['bytesPerCycle']
        NewTracePixel.numCycles = self.dataFile.numCycles
        NewTracePixel.firstCycleOffsetBytes = self.dataFile.header['firstCycleOffsetBytes']
        NewTracePixel.linesPerCycle = self.dataFile.header['linesPerCycle']

        NewTracePixels = [NewTracePixel.copy() for _ in range(len(validSuperPixelIDs))]

        superPixelNumPixels, superPixelNumPixelsIDs = np.unique(pixelReplacementMap[:, 1], return_counts=True)
        ia = np.where(np.isin(superPixelNumPixelsIDs, validSuperPixelIDs))[0]
        superPixelNumPixels = superPixelNumPixels[ia]

        for idx in range(len(NewTracePixels)):
            NewTracePixels[idx].superPixelId = validSuperPixelIDs[idx]
            NewTracePixels[idx].superPixelNumPixels = superPixelNumPixels[idx]
            NewTracePixels[idx].superPixelNumPixelsSelected = validCounts[idx]

        for lineIdx, lineZIdx in enumerate(self.dataFile.lineFastZIdxs):
            if lineZIdx != self.zIdx:
                continue

            lineSuperPixelIDs = self.dataFile.lineSuperPixelIDs[lineIdx]
            mask = np.isin(validSuperPixelIDs, lineSuperPixelIDs)

            byteOffsets = (np.where(mask)[0]) * 2
            byteOffsets += self.dataFile.lineDataNumElements[lineIdx] * 2 * (self.chIdx - 1)
            byteOffsets += self.dataFile.lineDataStartIdxs[lineIdx] * 2
            byteOffsets -= self.dataFile.header['firstCycleOffsetBytes']

            pixIdxs = np.where(mask)

            for idx in range(len(pixIdxs[0])):
                pixIdx = pixIdxs[0][idx]
                NewTracePixels[pixIdx].byteOffsets.append(byteOffsets[idx])
                NewTracePixels[pixIdx].lineIdxs.append(lineIdx)

        TracePixels = ExistingTracePixels + NewTracePixels
        TracePixels.sort(key=lambda x: x.superPixelId)
        return TracePixels

