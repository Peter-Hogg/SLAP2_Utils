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
        if ~np.any(rasterPixels):
            rasterPixels = np.array([])
        elif (isinstance(rasterPixels, np.ndarray) and np.issubdtype(rasterPixels.dtype, np.bool_)):
            rasterPixels = self.checkMapDims(rasterPixels)
            #rasterPixels = np.where(rasterPixels.ravel('f'))[0]+1
            rasterPixels = np.where(rasterPixels.ravel('f'))[0]

        if ~np.any(integrationPixels):
            integrationPixels = np.array([])
        elif  (isinstance(integrationPixels, np.ndarray) and np.issubdtype(integrationPixels.dtype, np.bool_)):
            integrationPixels = self.checkMapDims(integrationPixels)
            integrationPixels= np.where(integrationPixels.ravel('f'))[0]+int(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn'])+1

        pixelIdxs_ = np.uint32(np.concatenate((rasterPixels, integrationPixels), axis=None))

        self.TracePixels = self.getTracePixels(pixelIdxs_)

        self.pixelIdxs = pixelIdxs_

    def checkMapDims(self, map_):
        dmdPixelsPerRow = self.dataFile.header['dmdPixelsPerRow']
        dmdPixelsPerColumn = self.dataFile.header['dmdPixelsPerColumn']

    
        if dmdPixelsPerColumn != dmdPixelsPerRow and map_.shape == (dmdPixelsPerColumn, dmdPixelsPerRow):
            map_ = map_.T

        assert map_.shape == (dmdPixelsPerRow, dmdPixelsPerColumn), \
            f"Incorrect map size. Map needs to be size [{dmdPixelsPerRow},{dmdPixelsPerColumn}]"
        return map_

    def loadData(self):
        # probably unneeded. Trace Pixels load on process.
        self.TracePixels = self.TracePixels.load()

    def process(self, windowWidth_lines, expectedWindowWidth_lines):
        for i,j in enumerate(self.TracePixels):
            j.load()


        tempKernel = np.exp(-np.abs(np.arange(-4*windowWidth_lines, 4*windowWidth_lines+1) / windowWidth_lines))
        tempKernel = tempKernel.astype('float32')

        expectedKernel = np.ones(expectedWindowWidth_lines, dtype='float32')

        if self.dataFile.header['linesPerCycle'] == 0 or self.dataFile.numCycles == 0:
            numLines = 0
        else:
            numLines = int(self.dataFile.header['linesPerCycle'] * self.dataFile.numCycles)



        sumDataWeighted = np.zeros(numLines, dtype='float32')
        sumExpected = np.zeros(numLines, dtype='float32')
        sumExpectedWeighted = np.zeros(numLines, dtype='float32')

        for tracePix in self.TracePixels:
            lineData = np.zeros((int(self.dataFile.header['linesPerCycle']), int(self.dataFile.numCycles)), dtype='float32')
            sampled = np.zeros((int(self.dataFile.header['linesPerCycle']), int(self.dataFile.numCycles)), dtype='float32')

            lineData[tracePix.lineIdxs,:] = np.array(tracePix.data)
            sampled[tracePix.lineIdxs, :] = 1
            lineData = lineData.flatten('F')
            sampled = sampled.flatten('F')


            spatialWeight = tracePix.superPixelNumPixelsSelected / tracePix.superPixelNumPixels
            weightedData = np.convolve(lineData, tempKernel * spatialWeight, mode='same')



            tempWeights = np.convolve(sampled, tempKernel, mode='same')
            npad = len(expectedKernel) - 1

            
            expected = np.convolve(lineData, expectedKernel, mode='full')
            first = npad - npad//2
            expected=expected[first:first+len(lineData)]



            npad1 = len(expectedKernel) - 1
            expectedN = np.convolve(sampled, expectedKernel, mode='full')
            first2 = npad1 - npad1//2 
            expectedN=expectedN[first2:first2+len(sampled)]

            expected = expected / (expectedN + np.finfo(float).eps)

            expectedWeighted = expected * tempWeights
            sumDataWeighted = sumDataWeighted + weightedData
            sumExpected += expected
            sumExpectedWeighted += expectedWeighted

        trace = sumDataWeighted / (sumExpectedWeighted + np.finfo(float).eps) * sumExpected

        #To be added: slap2dataview post-process conditional

        return trace, sumDataWeighted, sumExpected, sumExpectedWeighted


    def processAsync(self, windowWidth_lines, expectedWindowWidth_lines):
        hFuture_ = self.TracePixels.processAsync(windowWidth_lines, expectedWindowWidth_lines)

        def finalize(hFuture):
            self.TracePixels, trace = hFuture.fetchOutputs()

        hFuture = hFuture_.afterAll(finalize, 1, PassFuture=True)
        return hFuture


    def getRawSuperPixel(self,superpixel=1):
        for j in self.TracePixels:
            if not j.loaded:
                print("You have not loaded the trace properly!")
                break 

        rawlist=[]
        if len(self.TracePixels[superpixel].data[0]) == 1:
            for i in range(len(self.TracePixels[superpixel].data)):
                rawlist.append(self.TracePixels[superpixel].data[i])
            return rawlist

        else:
            for i in range(len(self.TracePixels[superpixel].data)):
                for j in range(len(self.TracePixels[superpixel].data[i])):
                    rawlist.append(self.TracePixels[superpixel].data[i][j])
            return rawlist

    def getRawAverageSuperPixel(self,superpixel=1):
        for j in self.TracePixels:
            if not j.loaded:
                print("You have not loaded the trace properly!")
                break 

        if len(self.TracePixels[superpixel].data[0]) == 1:
            print("this is not a volumetric trace!")
            break
        else:
            for i in range(len(self.TracePixels[superpixel].data)):
                average=0
                for j in range(len(self.TracePixels[superpixel].data[i])):
                    average+=self.TracePixels[superpixel].data[i][j]
                average=round(average/3)
                rawlist.append(average)
            return rawlist
                



    def getTracePixels(self, pixelIdxs):
        pixelIDs = np.unique(pixelIdxs)

        for i in range(len(pixelIDs)):
            pixelIDs[i]=pixelIDs[i]-1

        dmdNumPix = self.dataFile.header['dmdPixelsPerRow'] * self.dataFile.header['dmdPixelsPerColumn']



        pixelReplacementMap = copy.deepcopy(self.dataFile.zPixelReplacementMaps[self.zIdx-1])
        #pixelReplacementMap = copy.deepcopy(self.dataFile.zPixelReplacementMaps)


        intMask = pixelReplacementMap[1,:] >= dmdNumPix

        j=0
        for i in intMask:
            if i:
                pixelReplacementMap[0,j]=pixelReplacementMap[0,j]+dmdNumPix
            j=j+1
        sortIdxs = np.argsort(pixelReplacementMap[0])

        idxs1=ismembc2(pixelIDs,pixelReplacementMap[0])
        validSuperPixelIDs =pixelReplacementMap[1,idxs1]
        validSuperPixelIDs, validCounts = np.unique(validSuperPixelIDs, return_counts=True)



        existingSuperPixelIDs = [pixel.superPixelId for pixel in self.TracePixels]
        C, ia, ib = np.intersect1d(validSuperPixelIDs, existingSuperPixelIDs, return_indices=True)

        validSuperPixelIDs = np.delete(validSuperPixelIDs, ia)
        validCounts = np.delete(validCounts, ia)
        
  
        ExistingTracePixels = [self.TracePixels[i] for i in ib]

        NewTracePixel = TracePixel()
        NewTracePixel.fileName = self.dataFile.filename
        NewTracePixel.bytesPerCycle = self.dataFile.header['bytesPerCycle']
        NewTracePixel.firstCycleOffsetBytes = self.dataFile.header['firstCycleOffsetBytes']
        NewTracePixel.numCycles = self.dataFile.numCycles
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
            byteOffsets = [x+ len(lineSuperPixelIDs) * 2 * (self.chIdx - 1) for x in byteOffsets]
            byteOffsets = [x+self.dataFile.lineDataStartIdxs[lineIdx] * 2 for x in byteOffsets]
 
            byteOffsets = [int (x-self.dataFile.header['firstCycleOffsetBytes']) for x in byteOffsets]
            pixIdxs = np.where(mask)
            pixIdxs= [int(x) for x in pixIdxs[0]]


            for i, x in enumerate (pixIdxs):
                
                NewTracePixels[x].byteOffsets.append(byteOffsets[pixIdxs.index(x)])
                NewTracePixels[x].lineIdxs.append(lineIdx)
                
                   

 
        for x in ExistingTracePixels:
            NewTracePixels.append(x)
        TracePixels=NewTracePixels
        sorted_trace_pixels = sorted(TracePixels, key=lambda x: x.superPixelId)
        return TracePixels


        # To Do
        def getAverageTrace(self):
            return None





def ismembc2(A, B):
    """
    Fast membership test for 2D arrays based on sorted order.
    Returns a boolean array indicating which rows of A are also present in B.
    Parameters:
    - A: 2D numpy array  totest for membership in B
    - B: 2D numpy array
    Returns:
    - boolean numpy array of shape (A.shape[0],)
    """
    # Ensure A and B are numpy arrays
    A = np.asarray(A)
    B = np.asarray(B)
    # Check dimensions

    # Sort rows for both A and B
    sorted_A = np.sort(A)
    sorted_B = np.sort(B)
    # Use numpy's in1d for 1D membership testing
    # Convert 2D to 1D by viewing in a structured format
    flag=[]
    for element in A:
        if element in B:
            flag.append(np.where(B==element)[0][0])

    return flag