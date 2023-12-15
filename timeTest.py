import dask
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt
import slap2_utils.datafile as slap2

from slap2_utils.subclasses.metadata import MetaData
from slap2_utils.functions.imagestacks import averageStack
from tifffile import imread, imwrite
from slap2_utils.functions.imagestacks import averageStackCPU, averageStackGPU, averageStackMemoryGPU
import time
start_time = time.time()

averageStackCPU('../Driekland_Stacks/Volume_20231215_123601_DMD1.tif')

print("--- %s seconds ---" % (time.time() - start_time))


start_time = time.time()

averageStackGPU('../Driekland_Stacks/Volume_20231215_123601_DMD1.tif')

print("--- %s seconds ---" % (time.time() - start_time))

start_time = time.time()

averageStackMemoryGPU('../Driekland_Stacks/Volume_20231215_123601_DMD1.tif')

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
