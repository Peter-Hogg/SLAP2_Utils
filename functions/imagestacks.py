import dask
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt
import SLAP2_Utils.datafile as slap2
import pyclesperanto_prototype as cle

from SLAP2_Utils.subclasses.metadata import MetaData
from tifffile import imread, imwrite


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