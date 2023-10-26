import dask
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt
import SLAP2_Utils.datafile as slap2

from SLAP2_Utils.subclasses.metadata import MetaData
from SLAP2_Utils.functions.imagestacks import averageStack
from tifffile import imread, imwrite
from SLAP2_Utils.functions.imagestacks import averageStack2, averageStackGPU
import time
start_time = time.time()

averageStack2('acquisition_20230216_130937_DMD1.tif')

print("--- %s seconds ---" % (time.time() - start_time))


start_time = time.time()

averageStackGPU('acquisition_20230216_130937_DMD1.tif')

print("--- %s seconds ---" % (time.time() - start_time))
"""
file_path = 'stack_20221222_114328_DMD1.tif'
start_time = time.time()
metadata = MetaData(file_path[:-4]+'.meta')
duration = metadata.acqDuration_s
xdim, ydim = metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][0][0], metadata.AcquistionContainter.ParsePlan['rasterSizeXY'][1][0]
linesPerFrame = metadata.AcquistionContainter.ParsePlan['linesPerFrame']
lineRate = metadata.AcquistionContainter.ParsePlan['lineRateHz']
linesPerCycle = metadata.AcquistionContainter.ParsePlan['linesPerCycle']
frameRate = (lineRate[0]/ydim)[0]
frameNumber = int(frameRate*duration)
cyclePeriod_s = linesPerCycle / lineRate

file_path = 'stack_20221222_114328_DMD1.tif'
frames = imread(file_path)
avgStack = np.zeros((int(frames.shape[0]/frameNumber), frames.shape[1], frames.shape[2]))
sliceStr, sliceStop = 0,0
for i in range(int(frames.shape[0]/frameNumber)):
    sliceStop = frameNumber*i
    avgStack[i, :, : ] = np.mean(frames[sliceStr:sliceStop, : ,:], axis=0)
    sliceStr = sliceStop
imwrite('average2_'+file_path, avgStack)
print("--- %s seconds ---" % (time.time() - start_time))
"""
