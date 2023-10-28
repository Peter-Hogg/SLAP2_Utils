import numpy as np


class Trace:
    def __init__(self, hDataFile, zIdx=1, chIdx=1):
        self.hDataFile = hDataFile
        self.zIdx = zIdx
        self.chIdx = chIdx
        self.TracePixels = []
        self.pixelIdxs = []

    @property
    def superPixelIds(self):
        return [pixel.superPixelId for pixel in self.TracePixels]

    def setPixelIdxs(self, rasterPixels=None, integrationPixels=None):
        def checkMapDims(map):
            dmdPixelsPerRow = self.hDataFile.header['dmdPixelsPerRow']
            dmdPixelsPerColumn = self.hDataFile.header['dmdPixelsPerColumn']

            if dmdPixelsPerColumn != dmdPixelsPerRow:
                if map.shape == (dmdPixelsPerColumn, dmdPixelsPerRow):
                    map = map.T

            assert map.shape == (dmdPixelsPerRow, dmdPixelsPerColumn), \
                f"Incorrect map size. Map needs to be size [{dmdPixelsPerRow},{dmdPixelsPerColumn}]"

            return map

        if rasterPixels is not None and isinstance(rasterPixels, bool):
            rasterPixels = checkMapDims(rasterPixels)
            rasterPixels = np.where(rasterPixels)

        if integrationPixels is not None and isinstance(integrationPixels, bool):
            integrationPixels = checkMapDims(integrationPixels)
            integrationPixels = np.where(integrationPixels) + np.prod(integrationPixels.shape)

        np.testing.assert_equal(isinstance(rasterPixels, (int, np.integer)), True, err_msg='rasterPixels')
        np.testing.assert_equal(isinstance(integrationPixels, (int, np.integer)), True, err_msg='integrationPixels')

        pixelIdxs_ = np.concatenate((rasterPixels.flatten(), integrationPixels.flatten()), axis=None).astype(np.uint32)

        self.TracePixels = self.getTracePixels(pixelIdxs_)
        self.pixelIdxs = pixelIdxs_

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
        dmdNumPix = self.hDataFile.header['dmdPixelsPerRow'] * self.hDataFile.header['dmdPixelsPerColumn']

        pixelReplacementMap = self.hDataFile.zPixelReplacementMaps[self.zIdx]
        intMask = pixelReplacementMap[:, 1] >= dmdNumPix
        pixelReplacementMap[intMask, 0] = pixelReplacementMap[intMask, 0] + dmdNumPix

        sortIdxs = np.argsort(pixelReplacementMap[:, 0])
        pixelReplacementMap = pixelReplacementMap[sortIdxs, :]
        idxs = np.where(np.isin(pixelIDs, pixelReplacementMap[:, 0]))[0]
        validMask = idxs > 0

        idxs = idxs[validMask]
        validSuperPixelIDs = pixelReplacementMap[idxs, 1]
        validCounts, validSuperPixelIDs = np.unique(validSuperPixelIDs, return_counts=True)

        existingSuperPixelIDs = [pixel.superPixelId for pixel in self.TracePixels]
        ia, ib = np.intersect1d(validSuperPixelIDs, existingSuperPixelIDs, return_indices=True)

        validSuperPixelIDs = np.delete(validSuperPixelIDs, ia)
        validCounts = np.delete(validCounts, ia)

        ExistingTracePixels = [self.TracePixels[i] for i in ib]

        NewTracePixel = TracePixel()
        NewTracePixel.fileName = self.hDataFile.filename
        NewTracePixel.bytesPerCycle = self.hDataFile.header['bytesPerCycle']
        NewTracePixel.numCycles = self.hDataFile.numCycles
        NewTracePixel.firstCycleOffsetBytes = self.hDataFile.header['firstCycleOffsetBytes']
        NewTracePixel.linesPerCycle = self.hDataFile.header['linesPerCycle']

        NewTracePixels = [NewTracePixel.copy() for _ in range(len(validSuperPixelIDs))]

        superPixelNumPixels, superPixelNumPixelsIDs = np.unique(pixelReplacementMap[:, 1], return_counts=True)
        ia = np.where(np.isin(superPixelNumPixelsIDs, validSuperPixelIDs))[0]
        superPixelNumPixels = superPixelNumPixels[ia]

        for idx in range(len(NewTracePixels)):
            NewTracePixels[idx].superPixelId = validSuperPixelIDs[idx]
            NewTracePixels[idx].superPixelNumPixels = superPixelNumPixels[idx]
            NewTracePixels[idx].superPixelNumPixelsSelected = validCounts[idx]

        for lineIdx, lineZIdx in enumerate(self.hDataFile.lineFastZIdxs):
            if lineZIdx != self.zIdx:
                continue

            lineSuperPixelIDs = self.hDataFile.lineSuperPixelIDs[lineIdx]
            mask = np.isin(validSuperPixelIDs, lineSuperPixelIDs)

            byteOffsets = (np.where(mask)[0]) * 2
            byteOffsets += self.hDataFile.lineDataNumElements[lineIdx] * 2 * (self.chIdx - 1)
            byteOffsets += self.hDataFile.lineDataStartIdxs[lineIdx] * 2
            byteOffsets -= self.hDataFile.header['firstCycleOffsetBytes']

            pixIdxs = np.where(mask)

            for idx in range(len(pixIdxs[0])):
                pixIdx = pixIdxs[0][idx]
                NewTracePixels[pixIdx].byteOffsets.append(byteOffsets[idx])
                NewTracePixels[pixIdx].lineIdxs.append(lineIdx)

        TracePixels = ExistingTracePixels + NewTracePixels
        TracePixels.sort(key=lambda x: x.superPixelId)
        return TracePixels

