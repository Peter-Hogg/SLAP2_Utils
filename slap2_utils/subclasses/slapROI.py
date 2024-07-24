class slapROI(): 
    def __init__(self, h5file, roiRef):
    """
        A class used to represent and manipulate a single trace pixel from a SLAP2 data file.
    
        Attributes
        ----------
        fileName : str
            The name of the file to be loaded.
        superPixelId : int
            The identifier for the superpixel.
        superPixelNumPixels : int
            The number of pixels in the superpixel.
        superPixelNumPixelsSelected : int
            The number of selected pixels in the superpixel.
        byteOffsets : list
            A list of byte offsets for data extraction.
        lineIdxs : list
            A list of line indices for data extraction.
        data : list
            The loaded data for the trace pixel.
        isLoaded : bool
            A flag indicating whether the data is loaded.
        firstCycleOffsetBytes : int
            The offset for the first cycle in bytes.
        numCycles : int
            The number of cycles.
        bytesPerCycle : int
            The number of bytes per cycle.
        linesPerCycle : int
            The number of lines per cycle.
        y : int
            An unspecified variable, initialized to -1.
        
    
        Descriptions for methods:
        ----------
               
                
        Methods
        ---------
        __init__() :
            Initialize the fields with values.
    
        Return
        -------
            Self with populated fields.
    
        Methods
        ---------
        load(hMemmap=None) :
            Loads the data for the trace pixel from the specified memory-mapped file, which is given as an input (hMemmap).
    
        Return
        -------
            Self with edited data field and isLoaded changed to true.
        
        """
        
        self.constructor = None
        self.roiType = None
        self.imageMode = None
        self.targetRate = None
        self.shapeData = None
        self.z = None
        
        self.constructor = ''.join([chr(_char[0]) for _char in h5file[roiRef]['constructor']])
        if 'Rectangle' in self.constructor:
            self.roiType = 'RectangleRoi'
        else:
            self.roiType = 'ArbitraryRoi'
        
        self.shapeData = h5file[roiRef]['shapeData'][:].copy()
        if h5file[roiRef]['imagingMode']['ClassName'][0][0] == 1:
            self.imageMode = "Raster"
        else:
            self.imageMode = 'Integrate'
        self.targetRate = h5file[roiRef]['targetRate'][0][0]
        self.z = h5file[roiRef]['z'][0][0]
