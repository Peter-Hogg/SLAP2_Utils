import sys
import apoc
import os
import time

import numpy as np
import pyclesperanto_prototype as cle
import napari

from skimage.io import imread
from skimage.morphology import skeletonize,binary_closing, skeletonize_3d,dilation, erosion, remove_small_objects, disk, square
from skimage import filters

from scipy.io import savemat
from skimage.measure import label, regionprops
from scipy import ndimage

from segment_anything import sam_model_registry, SamPredictor



def masked_sliding_window_inference(image, mask, segmenter, window_size=(256, 256), stride=128, ):
    h, w = image.shape[1:]
    output = np.zeros((image.shape[0], image.shape[1], image.shape[2]))
    for y in range(0, h-window_size[1]+1, stride):
        for x in range(0, w-window_size[0]+1, stride):
            if np.max(mask[y:y+window_size[1], x:x+window_size[0]]) == True:
                for z in range(0, output.shape[0]-1, 1):

                    patch = image[z, y:y+window_size[1], x:x+window_size[0]]
                    patch_output = segmenter.predict(patch)

                    # Handle overlap by averaging or other strategies
                    output[z, y:y+window_size[1], x:x+window_size[0]] = patch_output
    return output

def find_skeleton_3Dpoints(skelly_image):
    # Force binary image
    skelly_image[skelly_image>0]=1

    points = np.where(skelly_image==1)
    end_points = []
    y_points = []

    for point in range(len(points[0])):
        z = points[0][point]
        x = points[1][point]
        y = points[2][point]

        window=skelly_image[z-1:z+2, x-1:x+2, y-1:y+2]
        if np.sum(window)<=2:
            end_points.append((z,x,y))
        if np.sum(window)>=4:
            y_points.append((z,x,y))
    return end_points, y_points

def genDendriticRoi(imagepath):
    cl_filename = "test_object_segmenter_from_folders.cl"

    # Load Reference Stack to segment
    data1 = imread(imagepath)
    img_slice= data1[0,:,:,:]

    # Load Random Forest Pixel Classifier
    segmenter = apoc.PixelClassifier(opencl_filename=cl_filename)

    # Load up SAM to help select only neuron of interest
    sam_checkpoint = "checkpoints/sam_vit_l_0b3195.pth"
    model_type = "vit_l"
    device = "cuda"

    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    predictor = SamPredictor(sam)

    # Make 2D projection for SAM has to be RGB image
    projection = np.max(img_slice.astype('uint8'), axis=0)

    projectionRGB = np.array([projection.astype('uint8'), projection.astype('uint8'), projection.astype('uint8')])
    projectionRGB = np.moveaxis(projectionRGB, 0, 2)
    predictor.set_image(projectionRGB)

    # provide box for SAM
    with napari.gui_qt():
        boxSelector = napari.Viewer()
        boxSelector.add_image(projection, gamma=.35)
        boxSelector.add_shapes()

    while len(boxSelector.layers[1].data) < 1:
        time.sleep(1)
    input_box = boxSelector.layers[1].data[0].astype(int)
    input_box = [np.min(input_box[:, 1]),np.min(input_box[:, 0]),  np.max(input_box[:, 1]), np.max(input_box[:, 0])] #np.concatenate([input_box[0, :], input_box[2, :]])
    input_box = np.array(input_box)

    # Generate neuron mask with SAM
    masks, _, _ = predictor.predict(
                                    point_coords=None,
                                    point_labels=None,
                                    box=input_box,
                                    multimask_output=False)
    
    # Use the Random Forest
    labels = masked_sliding_window_inference(img_slice, masks[0], segmenter)
    labels[:, masks[0]==False] = 0

    # Prepare the neuron labels for ROI creation
    neuron = labels.copy()
    neuron[neuron!=2] = 0
    neuron[neuron==2] = 1
    neuron = ndimage.binary_fill_holes(neuron)
    neuron = remove_small_objects(neuron, 500, connectivity=10)
    neuron = filters.gaussian(neuron, .5)
    neuron[neuron >0] = 1
    neuron = neuron.astype(int)
    footprint = disk(3)

    # Preslice errosion to tighten things up
    for i in range(neuron.shape[0]):
        neuron[i, :,:] = erosion(neuron[i,:,:],footprint)
    skel=0
    skel = skeletonize_3d(neuron)
    
    # Find Junctions
    ends, junctions = find_skeleton_3Dpoints(skel)

    # Use the branch nodes to break up the skeleton into branches
    for _branchNode in junctions:
        skel[_branchNode[0], _branchNode[1], _branchNode[2]] = 0

    line_fragments = label(skel)
    lineInts = list(np.unique(line_fragments))
    lineInts.pop(0)
    SLAP2ROIs = np.zeros_like(neuron)
    roi=1
    footprint = square(15)

    for z in range(skel.shape[0]):
        line_fragments = label(skel[z, :, :])
        roiData = dilation(line_fragments, footprint)
        roiData = roiData * neuron[z, :, : ]
        SLAP2ROIs[z, :, :], _ = ndimage.label(roiData)

    labeled_array, num_features = ndimage.label(SLAP2ROIs)
    # Specify full connectivity for 3D (26-connectivity)
    structure = np.zeros((3, 3, 3), dtype=int)
    structure[1, :, :] = 1

    # Apply connected component labeling with the specified structure
    labeled_array, num_features = ndimage.label(SLAP2ROIs, structure=structure)
    newFilePath = os.path.join(os.path.split(imagepath)[0], 'averageGPU_'+os.path.basename(imagepath))

    newFilePath = os.path.join(os.path.split(imagepath)[0], '_autoROI_'+os.path.basename(imagepath))
    np.save(newFilePath[:-4]+'.npy', labeled_array)

    savemat(newFilePath[:-4]+'.mat', {'roi':labeled_array})



def main():
    # Loading bunch of stuff

    _imgpath = sys.argv[1]

    
    genDendriticRoi(_imgpath)

if __name__ == "__main__":
    main()