import dask
import os
import numpy as np 
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt
import SLAP2_Utils.datafile as slap2
import pyclesperanto_prototype as cle
import zarr
import dask_image.imread
from SLAP2_Utils.subclasses.metadata import MetaData
import tifffile 
from ScanImageTiffReader import ScanImageTiffReader

# Functions for generating an image stack from slice data by loading the tiff file into memory
def averageStackMemory(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][0][0], metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquistionContainter.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquistionContainter.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquistionContainter.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate

    frames = ScanImageTiffReader(path).data()

 
    avgStack = np.zeros((int(frames.shape[0]/frameNumber), frames.shape[1], frames.shape[2]))
    fStrt = frameNumber
    fStp = 0

    for i in range(int(frames.shape[0]/frameNumber)):
        avgStack[i, :,:  ] = np.mean(frames[fStp:fStrt, :,: ], axis=0)
        fStrt += frameNumber
        fStp += frameNumber

    print('average_'+os.path.basename(path))
    tifffile.imwrite('average_'+os.path.basename(path), avgStack)

def averageStackMemoryGPU(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][0][0], metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquistionContainter.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquistionContainter.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquistionContainter.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate

    
    frames = ScanImageTiffReader(path).data()
   
 
    avgStack = np.zeros((int(frames.shape[0]/frameNumber), frames.shape[1], frames.shape[2]))
    fStrt = frameNumber
    fStp = 0

    for i in range(int(frames.shape[0]/frameNumber)):
        try:
            avgStack[i, :,:  ] = cle.mean_z_projection(frames[fStp:fStrt, :,: ])
            fStrt += frameNumber
            fStp += frameNumber

        except:
            pass            

    print('average_'+os.path.basename(path))
    tifffile.imwrite('averageGPU_'+os.path.basename(path), avgStack)
    print('Stack Saved')
# Functions for generating an image stack from slice data without loading the tiff file into memory

def averageStack(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][0][0], metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquistionContainter.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquistionContainter.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquistionContainter.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate


    store = imread(path, aszarr=True)
    imagedata = da.from_zarr(store)
    imagedata = imagedata.rechunk((frameNumber, ydim, xdim))
    avgStack = np.zeros((1, int(imagedata.shape[0]/frameNumber), imagedata.shape[1], imagedata.shape[2]))

    @dask.delayed



    def returnSlice(_block):
        return np.mean(_block, axis=0)
    results = []
    for _block in imagedata.blocks:
        results.append(returnSlice(_block))



    avgStack = np.array(dask.compute(results))
    imwrite('average_'+path, avgStack)

def averageStackGPU(path):
    print(cle.available_device_names())
    cle.select_device("RTX")

    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][0][0], metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquistionContainter.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquistionContainter.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquistionContainter.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate


    store = imread(path, aszarr=True)
    imagedata = da.from_zarr(store)
    imagedata = imagedata.rechunk((frameNumber, ydim, xdim))
    avgStack = np.zeros((1, int(imagedata.shape[0]/frameNumber), imagedata.shape[1], imagedata.shape[2]))

    @dask.delayed
    def returnSlice(_block):
        return cle.mean_z_projection(_block)
    results = []
    for _block in imagedata.blocks:
        results.append(returnSlice(_block))



    avgStack = np.array(dask.compute(results))
    
    imwrite('average_'+path, avgStack)
