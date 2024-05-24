# Imports necessary libraries and initializes some variables.
import numpy as np
from .trace_pixel import TracePixel
import copy

class Trace:
    def __init__(self, dataFile, zIdx=0, chIdx=0):
        """
        Trace class contains the datafile and tracepixels of the provided ROI
        Returns:
        - Trace object with the following fields
        """
        # Initializes the Trace object with provided parameters.
        # Sets default values for TracePixels and pixelIdxs.
        self.dataFile = dataFile
        self.zIdx = zIdx
        self.chIdx = chIdx
        self.TracePixels = []
        self.pixelIdxs = []

    @property
    # Defines a property superPixelIds that returns a list of superpixel IDs.
    def superPixelIds(self):
        return [pixel.superPixelId for pixel in self.TracePixels]

    
    # Sets pixel indexes based on provided raster and integration pixel maps from the input.
    # TracePixels are called after pixelIdxs are provided.
    def setPixelIdxs(self, rasterPixels=None, integrationPixels=None):
        """
        setPixelIdxs sets up the masks for the provided ROI if it is not provided 
        (default is all true) and check whether the provided masks are correct in 
        its dimensions. It then calls getTracePixelsto set up initial fields and 
        properties of individual superpixels in a ROI.
        Returns:
        - Trace object with loaded TracePixels and pixelIdxs
        """
        
        if ~np.any(rasterPixels):
            rasterPixels = np.array([])
            
        elif (isinstance(rasterPixels, np.ndarray) and np.issubdtype(rasterPixels.dtype, np.bool_)):
            rasterPixels = self.checkMapDims(rasterPixels)
            rasterPixels = np.where(rasterPixels.ravel('f'))[0]

        if ~np.any(integrationPixels):
            integrationPixels = np.array([])
            
        elif  (isinstance(integrationPixels, np.ndarray) and np.issubdtype(integrationPixels.dtype, np.bool_)):
            integrationPixels = self.checkMapDims(integrationPixels)
            integrationPixels= np.where(integrationPixels.ravel('f'))[0]+int(self.dataFile.header['dmdPixelsPerRow']*self.dataFile.header['dmdPixelsPerColumn'])+1

        pixelIdxs_ = np.uint32(np.concatenate((rasterPixels, integrationPixels), axis=None))

        # Loads up tracepixels using the getTracePixels function
        self.TracePixels = self.getTracePixels(pixelIdxs_)

        self.pixelIdxs = pixelIdxs_

    
    def checkMapDims(self, map_):
        """
        checkMapDims checks and adjusts the dimensions of a map 
        based on DMD (Digital Micromirror Device) pixel parameters.
        Returns:
        - map (adjusted map if its shape was incorrect or inverted)
        """
        
        dmdPixelsPerRow = self.dataFile.header['dmdPixelsPerRow']
        dmdPixelsPerColumn = self.dataFile.header['dmdPixelsPerColumn']

        # Check both ways: if one way does not match up, check whether the shape fits the transposed version
        if dmdPixelsPerColumn != dmdPixelsPerRow and map_.shape == (dmdPixelsPerColumn, dmdPixelsPerRow):
            map_ = map_.T

        assert map_.shape == (dmdPixelsPerRow, dmdPixelsPerColumn), \
            f"Incorrect map size. Map needs to be size [{dmdPixelsPerRow},{dmdPixelsPerColumn}]"
        return map_

    
    # This is a bit different from MatLab version due to the inherent object-oriented programming difference.
    def process(self, windowWidth_lines, expectedWindowWidth_lines):
        """
        process actually loads the pre-set up TracePixels by calling its sub-functions.
        It then deconvolve the data to fill the gaps that occurs as highlighted in parse plan.
        Returns:
        - trace (convolved version), the parameters used (sumDataWeighted, sumExpected, sumExpectedWeighted)
        """
        
        for i,j in enumerate(self.TracePixels):
            j.load()

        #Different convolution algorithms are applied to compensate for the inconsistent interval in data
        tempKernel = np.exp(-np.abs(np.arange(-4*windowWidth_lines, 4*windowWidth_lines+1) / windowWidth_lines))
        tempKernel = tempKernel.astype('float32')

        expectedKernel = np.ones(expectedWindowWidth_lines, dtype='float32')

        if self.dataFile.header['linesPerCycle'] == 0 or self.dataFile.numCycles == 0:
            numLines = 0
        else:
            numLines = int(self.dataFile.header['linesPerCycle'] * self.dataFile.numCycles)

        # All 3 sum variables here are utilized for deconvolution algorithm
        sumDataWeighted = np.zeros(numLines, dtype='float32')
        sumExpected = np.zeros(numLines, dtype='float32')
        sumExpectedWeighted = np.zeros(numLines, dtype='float32')


        # Getting the lane data and convolving the data
        for tracePix in self.TracePixels:
            lineData = np.zeros((int(self.dataFile.header['linesPerCycle']), int(self.dataFile.numCycles)), dtype='float32')
            sampled = np.zeros((int(self.dataFile.header['linesPerCycle']), int(self.dataFile.numCycles)), dtype='float32')

            lineData[tracePix.lineIdxs,:] = np.array(tracePix.data)
            sampled[tracePix.lineIdxs, :] = 1
            lineData = lineData.flatten('F')
            sampled = sampled.flatten('F')

            # Calculation are based on expected and expectedN
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

        # Reconstruct the trace here
        trace = sumDataWeighted / (sumExpectedWeighted + np.finfo(float).eps) * sumExpected

        # To be added: slap2dataview post-process conditional

        return trace, sumDataWeighted, sumExpected, sumExpectedWeighted


    def getRawSuperPixel(self,superpixel=1):
        """
        getRawSuperPixel obtains the raw data instead of the convolved data.
        Returns:
        - rawlist, which contains the raw data from the data file
        """
        for j in self.TracePixels:
            if not j.loaded:
                print("You have not loaded the trace properly!")
                break 

        rawlist=[]

        # Loop through the data, see if it is volumetric or not
        # This is for non volumetric
        if len(self.TracePixels[superpixel].data[0]) == 1:
            for i in range(len(self.TracePixels[superpixel].data)):
                rawlist.append(self.TracePixels[superpixel].data[i])
            return rawlist

        # This is for volumetric
        else:
            for i in range(len(self.TracePixels[superpixel].data)):
                for j in range(len(self.TracePixels[superpixel].data[i])):
                    rawlist.append(self.TracePixels[superpixel].data[i][j])
            return rawlist

    
    def getRawAverageSuperPixel(self,superpixel=1):
        """
        getRawAverageSuperPixels only works for volumetric trace. It averages 
        all superpixels in an ROI together. 
        Returns:
        - rawlist, which contains the averaged data from the data file
        """
        
        rawlist = []

        # Sanity check for inputs
        for j in self.TracePixels:
            if not j.loaded:
                print("You have not loaded the trace properly!")
                break 

            if len(self.TracePixels[superpixel].data[0]) == 1:
                print("this is not a volumetric trace!")
                break

        # Loading the average of the superpixel in volumetric trace
        else:
            for i in range(len(self.TracePixels[superpixel].data)):
                average=0
                for j in range(len(self.TracePixels[superpixel].data[i])):
                    average+=self.TracePixels[superpixel].data[i][j]
                average=round(average/3)
                rawlist.append(average)
            return rawlist

    
    # A function that stores the order of the superpixel in an roi. How it is stored and retrieved from the memory is unordered
    def orderadjust(self):
        """
        orderadjust adjusts how tracepixels are indexed inside the TracePixels field because it could be unordered.
        The original order is based on size, which creates the case where pixels of (x,y) = (300.400) are indexed 
        in front of pixels with (x,y) = (200,500), although pixels of 500 in y are examined first in SLAP2.
        Returns:
        - TracePixels of sorted order
        """
        
        # Here we are using math to calculate the y index of the data
        for pixels in self.TracePixels:
            pixels.y =(pixels.superPixelId - 1024000) % 1280

        # Sorting the data according to y index
        ordered_trace = sorted(self.TracePixels, key=lambda trace_pixel:trace_pixel.y)

        # Replacing nonordered data here
        self.TracePixels = ordered_trace


    def getTracePixels(self, pixelIdxs):
        """
        getTracePixels sets up the initial TracePixel fields, such as how many there should be, its initial
        fields (like dmdNumPix), loading superpixelIDs in tracepixel, and adds new tracepixels on top of existing
        superpixels.
        Returns:
        - TracePixels with old TracePixels and new TracePixels
        """

        # Get unique pixel indices and adjust for 0-based indexing
        pixelIDs = np.unique(pixelIdxs)
        for i in range(len(pixelIDs)):
            pixelIDs[i] = pixelIDs[i] - 1

        # Load DMD (Digital Micro-mirror Device) pixel data
        dmdNumPix = self.dataFile.header['dmdPixelsPerRow'] * self.dataFile.header['dmdPixelsPerColumn']
        pixelReplacementMap = copy.deepcopy(self.dataFile.zPixelReplacementMaps[self.zIdx - 1])

        # Identify pixels that exceed the number of DMD pixels
        intMask = pixelReplacementMap[1, :] >= dmdNumPix

        # Adjust pixelReplacementMap for these identified pixels
        j = 0
        for i in intMask:
            if i:
                pixelReplacementMap[0, j] = pixelReplacementMap[0, j] + dmdNumPix
            j = j + 1

        # Sort pixelReplacementMap by the first column
        sortIdxs = np.argsort(pixelReplacementMap[0])

        # Find superpixel IDs corresponding to the given pixel indices
        idxs1 = ismembc2(pixelIDs, pixelReplacementMap[0])
        validSuperPixelIDs = pixelReplacementMap[1, idxs1]
        validSuperPixelIDs, validCounts = np.unique(validSuperPixelIDs, return_counts=True)

        # Extract existing superpixel IDs from TracePixels
        existingSuperPixelIDs = [pixel.superPixelId for pixel in self.TracePixels]

        # Find intersection of valid and existing superpixel IDs
        C, ia, ib = np.intersect1d(validSuperPixelIDs, existingSuperPixelIDs, return_indices=True)

        # Remove intersecting IDs from validSuperPixelIDs and validCounts
        validSuperPixelIDs = np.delete(validSuperPixelIDs, ia)
        validCounts = np.delete(validCounts, ia)

        # Retrieve the corresponding existing TracePixels
        ExistingTracePixels = [self.TracePixels[i] for i in ib]

        # Initialize new TracePixel
        NewTracePixel = TracePixel()
        NewTracePixel.fileName = self.dataFile.filename
        NewTracePixel.bytesPerCycle = self.dataFile.header['bytesPerCycle']
        NewTracePixel.firstCycleOffsetBytes = self.dataFile.header['firstCycleOffsetBytes']
        NewTracePixel.numCycles = self.dataFile.numCycles
        NewTracePixel.linesPerCycle = self.dataFile.header['linesPerCycle']

        # Create a list of new TracePixels based on the valid superpixel IDs
        NewTracePixels = [copy.deepcopy(NewTracePixel) for x in range(len(validSuperPixelIDs))]

        # Get the number of pixels per superpixel ID
        superPixelNumPixelsIDs, superPixelNumPixels = np.unique(pixelReplacementMap[1], return_counts=True)

        # Filter to include only valid superpixel IDs
        ia = np.where(np.isin(superPixelNumPixelsIDs, validSuperPixelIDs))[0]
        superPixelNumPixels = superPixelNumPixels[ia]

        # Assign superpixel data to new TracePixels
        for idx in range(len(NewTracePixels)):
            NewTracePixels[idx].superPixelId = validSuperPixelIDs[idx]
            NewTracePixels[idx].superPixelNumPixels = superPixelNumPixels[idx]
            NewTracePixels[idx].superPixelNumPixelsSelected = validCounts[idx]

        # Iterate over line superpixel IDs and process them
        for lineIdx in range(len(self.dataFile.lineSuperPixelIDs)):
            lineZIdx = self.dataFile.lineFastZIdxs[lineIdx]

            # Skip lines that do not match the current z-index
            if int(lineZIdx) != self.zIdx:
                continue

            lineSuperPixelIDs = self.dataFile.lineSuperPixelIDs[lineIdx][0]
            mask = np.isin(validSuperPixelIDs, lineSuperPixelIDs)

            positions = []
            for i in range(len(mask)):
                if mask[i]:
                    firstocc = np.where(lineSuperPixelIDs == validSuperPixelIDs[i])
                    positions.append(firstocc[0][0] + 1)

            # Calculate byte offsets for the valid positions
            byteOffsets = [(x - 1) * 2 for x in positions]
            byteOffsets = [x + len(lineSuperPixelIDs) * 2 * (self.chIdx - 1) for x in byteOffsets]
            byteOffsets = [x + self.dataFile.lineDataStartIdxs[lineIdx] * 2 for x in byteOffsets]
            byteOffsets = [int(x - self.dataFile.header['firstCycleOffsetBytes']) for x in byteOffsets]

            pixIdxs = np.where(mask)
            pixIdxs = [int(x) for x in pixIdxs[0]]

            # Assign byte offsets and line indices to the new TracePixels
            for i, x in enumerate(pixIdxs):
                NewTracePixels[x].byteOffsets.append(byteOffsets[pixIdxs.index(x)])
                NewTracePixels[x].lineIdxs.append(lineIdx)

        # Append existing TracePixels to the list of new TracePixels
        for x in ExistingTracePixels:
            NewTracePixels.append(x)

        # Sort the TracePixels by superPixelId
        TracePixels = NewTracePixels
        sorted_trace_pixels = sorted(TracePixels, key=lambda x: x.superPixelId)

        return TracePixels


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
