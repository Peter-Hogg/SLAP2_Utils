class slapROI(): 
    def __init__(self, h5file, roiRef):
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