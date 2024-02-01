import sys
import dask
import os
import numpy as np 
import cupy as cu
import dask.array as da
import numpy as np
import matplotlib.pyplot as plt
import slap2_utils.datafile as slap2
import pyclesperanto_prototype as cle
import zarr
import dask_image.imread
from slap2_utils.subclasses.metadata import MetaData
import tifffile 
from ScanImageTiffReader import ScanImageTiffReader

# Functions for generating an image stack from slice data by loading the tiff file into memory
def averageStackMemory(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][0][0], metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquisitionContainer.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquisitionContainer.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquisitionContainer.ParsePlan['linesPerCycle']
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
    xdim, ydim = metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][0][0], metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquisitionContainer.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquisitionContainer.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquisitionContainer.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate

    
    frames = ScanImageTiffReader(path).data()
   
 
    avgStack = np.zeros((int(frames.shape[0]/frameNumber), frames.shape[1], frames.shape[2]))
    fStrt = frameNumber
    fStp = 0

    for i in range(int(frames.shape[0]/frameNumber)):
        try:
            avgStack[i, :,:  ] = cu.mean(frames[fStp:fStrt, :,: ], axis=0)
            fStrt += frameNumber
            fStp += frameNumber

        except:
            pass            

    print('average_'+os.path.basename(path))
    tifffile.imwrite('averageGPU_'+os.path.basename(path), avgStack)
    print('Stack Saved')
    
# Functions for generating an image stack from slice data without loading the tiff file into memory
# Functions for generating an image stack from slice data without loading the tiff file into memory
def averageStackCPU(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][0][0], metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquisitionContainer.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquisitionContainer.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquisitionContainer.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate
    

    # Read image data and rechunk
    with tifffile.imread(path, aszarr=True) as zarr_store:
        imagedata = da.from_zarr(zarr_store)
        print(frameNumber, ydim, xdim)
        # Ensure the data is rechunked properly
        imagedata = imagedata.rechunk((frameNumber, ydim, xdim))
        
        z_slices = imagedata.shape[0] // frameNumber
        remaining_frames = imagedata.shape[0] % frameNumber
       
        complete_slices_data = imagedata[:z_slices*frameNumber]
        remaining_data = imagedata[z_slices*frameNumber:]

        # Reshape the complete slices data
        complete_slices_reshaped = complete_slices_data.reshape((z_slices, frameNumber, ydim, xdim))
        avg_complete_slices = da.mean(complete_slices_reshaped, axis=1)
        
        # Average the remaining data
        avg_remaining = da.mean(remaining_data, axis=0)
        avg_remaining = avg_remaining[None, ...]  # Add an additional dimension to match the shape of avg_complete_slices
       

        # Concatenate the results
        final_avg_stack = da.concatenate([avg_complete_slices, avg_remaining], axis=0)
        

   
        # Compute the result and save it
        final_avg_stack_result = final_avg_stack.compute()
        tifffile.imwrite('averageCPU_' + os.path.basename(path), final_avg_stack_result)


def averageStack(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][0][0], metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquisitionContainer.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquisitionContainer.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquisitionContainer.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate


    store = tifffile.imread(path, aszarr=True)
    imagedata = da.from_zarr(store)
    imagedata = imagedata.rechunk((frameNumber, ydim, xdim))
    avgStack = np.zeros(( int(imagedata.shape[0]/frameNumber), imagedata.shape[1], imagedata.shape[2]))
    print(imagedata.shape)
    print(avgStack.shape)
    @dask.delayed



    def returnSlice(_block):
        return np.mean(_block, axis=0)
    results = []
    for _block in imagedata.blocks:
        results.append(returnSlice(_block))



    avgStack = np.array(dask.compute(results))
    imwrite('average_'+path, avgStack)

def averageStackGPU(path):
    metadata = MetaData(path[:-4]+'.meta')
    duration = metadata.acqDuration_s
    xdim, ydim = metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][0][0], metadata.AcquisitionContainer.ParsePlan['rasterSizeXY'][1][0]
    linesPerFrame = metadata.AcquisitionContainer.ParsePlan['linesPerFrame']
    lineRate = metadata.AcquisitionContainer.ParsePlan['lineRateHz']
    linesPerCycle = metadata.AcquisitionContainer.ParsePlan['linesPerCycle']
    frameRate = (lineRate[0]/ydim)[0]
    frameNumber = int(frameRate*duration)
    cyclePeriod_s = linesPerCycle / lineRate


    store = tifffile.imread(path, aszarr=True)
    imagedata = da.from_zarr(store)
    imagedata = imagedata.rechunk((frameNumber, ydim, xdim))
    avgStack = np.zeros((1, int(imagedata.shape[0]/frameNumber), imagedata.shape[1], imagedata.shape[2]))

    @dask.delayed
    def returnSlice(_block):
        return cu.mean(_block, axis=0)
    results = []
    for _block in imagedata.blocks:
        results.append(returnSlice(_block))



    avgStack = np.array(dask.compute(results))
    newFilePath = os.path.join(os.path.split(path)[0], 'averageGPU_'+os.path.basename(path))
    tifffile.imwrite(newFilePath, avgStack)
    return newFilePath

def main():
    if len(sys.argv)<2:
        print('No path to tif file given')
        sys.exit(1)
    tifPath = sys.argv[1]
    averageStackGPU(tifPath)

if __name__ == "__main__":
    main()