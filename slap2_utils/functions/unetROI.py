import math
import matplotlib.pyplot as plt
import matplotlib.colors as mplc
from matplotlib import cm
import numpy as np
import numpy.ma as ma 
import napari
import os
import pandas as pd
import random
import subprocess
import time

from aicsimageio import AICSImage, imread 
from scipy.ndimage import center_of_mass
from scipy.ndimage import shift as img_shift
from scipy.signal import correlate2d
from scipy.signal import correlate2d
from math import isclose 
from scipy.stats.mstats import pearsonr
from PIL import Image, ImageDraw
from skimage.io import imsave
from skimage.filters import threshold_otsu, gaussian
from skimage.morphology import medial_axis, skeletonize,binary_closing, skeletonize_3d,dilation, erosion, remove_small_objects
from skimage.registration import phase_cross_correlation
from skimage.segmentation import flood_fill
from scipy import ndimage as ndi
from skimage import color
from sklearn import neighbors
from scipy.spatial import distance, KDTree
from skimage import data, util, filters, color
from skimage.segmentation import watershed, random_walker
from skimage.measure import label, regionprops
import skimage.measure as measure

# import processing functions
from processing.processing_functions import *

from DouglasPeucker import DouglasPeucker

# import machine learning modules
import torch
from torchvision import transforms, utils
from torch.utils.data import DataLoader
from monai.networks.nets import UNet
from monai.inferers.inferer import SliceInferer



def model_predict(image, mode, spatial_dim):
    path = os.getcwd()

    if spatial_dim == 3:
        # use AI assistance
        lateral_steps = 64
        axial_steps = 16
        patch_size = (axial_steps, lateral_steps, lateral_steps)
        batch_size = 64
        dim_order = (0,4,1,2,3)
        orig_shape = image.shape
        
        patch_transform = transforms.Compose([MinMaxScalerVectorized(),
                                patch_imgs(xy_step = lateral_steps, z_step = axial_steps, patch_size = patch_size, is_mask = False)])

        processed_test_img = MyImageDataset(raw_img = image,
                                            transform = patch_transform,
                                            img_order = dim_order)
        
        # img_dataloader = DataLoader(processed_test_img, batch_size = 1)

        reconstructed_img = inference(processed_test_img,f'{path}/models/{mode}.onnx', batch_size, patch_size, orig_shape)
        reconstructed_img = reconstructed_img.astype(int)

        # soma category is inferenced for only "Neuron" => change all the soma labels (1) to dendrite labels (2)
        if len(np.unique(reconstructed_img)) == 2:
            reconstructed_img[reconstructed_img==1] = 2
            return reconstructed_img, len(np.unique(reconstructed_img))+1
        else:
            return reconstructed_img, len(np.unique(reconstructed_img))

    if spatial_dim == 2:
        # currently lateral steps are fixed as 512 due to the model being trained on full slices of 512x512.
        model_path = f'{path}/models/2D_{mode}.pth'

        checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        lateral_steps = 512
        patch_size = (lateral_steps, lateral_steps)
        batch_size = 1
        input_chnl = 1
        output_chnl = 4
        norm_type = "batch"
        dropout = 0.1

        model = UNet(spatial_dims=2, 
                    in_channels = input_chnl,
                    out_channels = output_chnl,
                    channels = (32, 64, 128, 256, 512),
                    strides=(2, 2, 2, 2),
                    num_res_units=2,
                    norm = norm_type,
                    dropout = dropout)

        try :

            print('GPU used')
            print(torch.device("cuda"))
 
            device = torch.device("cuda")
            model.load_state_dict(torch.load(model_path, map_location="cuda:0"))
            model = model.to(device)
        except:
            model.load_state_dict(checkpoint['model_state_dict'])
            print('CPU used')
            model = model.to('cpu')
        inferer = SliceInferer(roi_size=patch_size, sw_batch_size=batch_size, spatial_dim = 0, progress = True)

        raw_transform = transforms.Compose([MinMaxScalerVectorized()])
        processed_img_dataset = WholeVolumeDataset(raw_img=image,
                                           raw_transform=raw_transform)
        
        processed_img, _ = next(iter(processed_img_dataset))
        processed_img = torch.unsqueeze(processed_img, dim = 0)

        with torch.no_grad():
            output = inferer(inputs = processed_img, network=model)
            print(output.shape)
            probabilities = torch.softmax(output,1)
            print(probabilities.shape)
            pred = to_numpy(torch.argmax(probabilities, 1)).astype(np.int16)

        # soma category is inferenced for only "Neuron" => change all the soma labels (1) to dendrite labels (2)
        if len(np.unique(pred)) == 2:
            pred[pred==1] = 2
            return pred, len(np.unique(pred))+1
        else:
            return pred, len(np.unique(pred))

def sliding_window_inference(image, window_size=(512, 512), stride=256):
    h, w = image.shape[1:]
    output = np.zeros((1,  image.shape[0],image.shape[1], image.shape[2]))

    for y in range(0, h-window_size[1]+1, stride):
        for x in range(0, w-window_size[0]+1, stride):
            patch = image[:, y:y+window_size[1], x:x+window_size[0]]
            
            # Predict using your model
            # You might need to add code here to adjust the shape or channel of the patch
            # e.g., patch = np.expand_dims(patch, axis=0)
            patch_output, _ = model_predict(patch,"Soma+Dendrite", 2)
            
            # Handle overlap by averaging or other strategies
            print(patch_output.shape)
            output[:, :, y:y+window_size[1], x:x+window_size[0]] = patch_output

    return output

def returnpoints_3D(array):
    test_array =array.copy()
    window = np.zeros([3,3])
    points = []
    for z in range(test_array.shape[0]):
        for i in range(array.shape[1]-3):
            for j in range(array.shape[2]-3):
                if test_array[z,i+1,j+1]==1:
                    window=test_array[z,i:i+3, j:j+3]
                    if np.sum(window)<=3:
                        if False ==((window[0,0]==True and window[2,2]==True) or (window[0,2]==True and window[2,0]==True)):

                            if np.sum(window[1,:])<=2 and  np.sum(np.sum(window[:,1]))<=2:
                                points.append((z,i+1,j+1))
    return points
                                              
                                              
def returnpoints_2D(array):
    test_array =array.copy()
    window = np.zeros([3,3])
    points = []
    for i in range(array[1]-3):
        for j in range(array[2]-3):
            if test_array[i+1,j+1]==1:
                window=test_array[i:i+3, j:j+3]
                if np.sum(window)<=3:
                    if False ==((window[0,0]==True and window[2,2]==True) or (window[0,2]==True and window[2,0]==True)):

                        if np.sum(window[1,:])<=2 and  np.sum(np.sum(window[:,1]))<=2:
                            points.append((j+1,i+1))
    return points

def seg_skel(image, img2skel, twoD=True):
    # Takes an skeletonized image and segments the skeleton per plan
    # Returns segs as unique values in 3D array
    
    # 3D per volume
    if twoD==False:
        print('Skeltonize in 3D')
        skel = skeletonize_3d(img2skel)
    
    # 2D per plane
    if twoD==True:
        img2skel = img2skel/np.max(img2skel)
        skel = np.zeros(img2skel.shape)
        for u in range(img2skel.shape[0]):
            skel[u,:,:]  = skeletonize(img2skel[u,:,:])
    segsperplane = np.zeros(img2skel.shape)
    for i in range(skel.shape[0]):
        edges = filters.sobel(skel[i,:,:])
        plane = skel[i,:,:]
        seeds = np.zeros((img2skel.shape[1:]))
        foreground, background = 1, 2
        seeds[plane <.5] = background
        seeds[skel[i,:,:] > .5] = foreground
        ws = watershed(edges, seeds)
        segments = measure.label(ws == foreground)
        temp_max = np.max(segsperplane)
        segments = segments+temp_max
        segments[segments ==temp_max]=0
        segsperplane[i,:,:] = segments
    return segsperplane

def locationMinus(A, B):
    return (A[0] - B[0], A[1] - B[1])

def normDelta(p1, p2):
    x, y = locationMinus(p1, p2)
    sz = math.sqrt(x*x + y*y)
    if sz ==0:
        sz=1
    return (x/sz, y/sz,)

# Given a selected point and an additional neightboring point
# returns a point perpendicular to the line joining these points
def caliperPoints(origin, point, ifNext):
    x, y =  normDelta(point, origin)
    if ifNext:
        vector = np.array([y, -x])
    else:
        vector = np.array([-y, x])
    return vector

def return_corners(firstP, secP):

    pC = caliperPoints(firstP, secP, ifNext=False)
    pCprime = pC * 3
    radiiPoint = pCprime+firstP
    negRadiiPoint = -pCprime +firstP

    negX = int(negRadiiPoint[0])
    posX = int(radiiPoint[0])
    posY = int(negRadiiPoint[1])
    negY = int(radiiPoint[1])
    

    
    return(negX, posY, posX, negY)

def segmentGen(t1, t2, plane):


    x1, y1, x2, y2 = return_corners(t1, t2)
    x3, y3, x4, y4 = return_corners(t2, t1)


    polygon = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
    img = Image.new('L', (plane.shape[1], plane.shape[0]), 0)
    ImageDraw.Draw(img).polygon(polygon, outline=1, fill=1)
    block = np.array(img)
    binary_image = plane.copy()
    binary_image[binary_image>0]=1
    segment = block*binary_image
    return block, segment

def return_smaller_seg(p1, p2, threshold, midpoints):
    if round(math.hypot(p1[1] - p2[1], p1[0] - p2[0])) > threshold:
        mp = (round((p1[0] + p2[0])/2), round((p1[1] + p2[1])/2))
        fp = p1
        subpoint1 = return_smaller_seg(fp, mp, threshold, midpoints)
        if subpoint1 is False:
            midpoints.append(mp)
        sp = p2
        subpoint2 = return_smaller_seg(mp, sp, threshold, midpoints)
         
        if subpoint2 is False:
            midpoints.append(mp)
        return midpoints
    else:
        return False

def find_skeleton_points(points, skelly_image):
    skelly_image[skelly_image>0]=1
    end_points = []
    y_points = []

    for point in range(points[0].shape[0]):
        i = points[0][point]
        j = points[1][point]
        window=skelly_image[i-1:i+2, j-1:j+2]
        '''        if False ==((window[0,0]==True and window[2,2]==True) or (window[0,2]==True and window[2,0]==True)):
            if np.sum(window[1,:])<=2 and  np.sum(np.sum(window[:,1]))<=2:
                end_points.append((j,i))'''
        if np.sum(window)<=2:
            end_points.append((j,i))
        if np.sum(window)==4:
            y_points.append((j,i))
    return end_points, y_points

def generateROIs(IMAGE, PIX = 10):
    data1 = imread(IMAGE)
    print(data1.shape)
    img_slice= data1[0,0,:,:,:]
    print(img_slice.shape)
    labels = sliding_window_inference(img_slice)
    print(labels.shape)
    test = napari.Viewer()

    #test.add_labels(segsperplane, name='Segments', scale=(5, 1, 1), blending='additive')
    test.add_labels(labels.astype(int), name='ROI', scale=(5, 1, 1), blending='additive')
    if not os.path.exists('results/'):
        os.makedirs('results')

    image = data1[0,0,:,:,:]
    dendrites = np.zeros_like(labels[0,:,:,:])
    dendrites[labels[0,:,:,:]==2]=1
    dendrites = np.array(dendrites, bool)
    dendrites = remove_small_objects(dendrites, 500, connectivity=10)

    neuron_mask = dendrites
    segsperplane = seg_skel(image, dendrites, False)
    segsperplane = segsperplane.astype(int)

    # Start timer to measure segmentation time
    start = time.time()

    SLAP_ROI = np.zeros(segsperplane.shape)
    SLAP_Blocks = np.zeros(segsperplane.shape)
    roi_ID = 2
    DP_Value = 1
    for z in range(segsperplane.shape[0]):
        
        
        segs_colors = np.unique(segsperplane[z,:,:]).astype(int)
        
        
        
        for i in segs_colors[1:]:
            plane = segsperplane[z,:,:].copy()
            plane[plane !=i]=0
            plane[plane>0]=1
            points = np.where(plane==1)

            endpoints, junctions = find_skeleton_points(points, plane)


            if len(junctions) > 0:
                #print("this many y-junctions", len(junctions))
                for junc in junctions:
                    plane[junc[1], junc[0]] = 0
                line_fragments = measure.label(plane)

                cut_lines = np.unique(line_fragments).astype(int)
                for line in cut_lines[1:]:
                    subplane = line_fragments.copy()

                    subplane[subplane !=line]=0
                    subplane[subplane>0]=1

                    points = np.where(subplane==1)

                    endpoints, junctions = find_skeleton_points(points, plane)

                    if len(endpoints)>1:
                        #print(endpoints)
                        points  = list(zip(points[1], points[0]))
                        points =  DouglasPeucker(points, 1)
                        pointArray = np.array(points)
                        sortedPoints = np.zeros_like(pointArray)
                        kdTree = KDTree(pointArray)
                        for i, c in enumerate(kdTree.query([0,0], k=pointArray.shape[0])[1]):
                            sortedPoints[i, : ] = pointArray[c, :]

                        for v in range(sortedPoints.shape[0]-1):
                            block, _ =  segmentGen(sortedPoints[v,:], sortedPoints[v+1,:], dendrites[z, :, :])
                            flipped =block
                            oneSeg = flipped*dendrites[z, :, :]
                            oneSeg = dilation(oneSeg)
                            flipped[flipped >0]= roi_ID
                            oneSeg[oneSeg >0]= roi_ID
                            roi_ID += 1
                            SLAP_Blocks[z, :, :] = SLAP_Blocks[z, :, :] + flipped
                            SLAP_ROI[z, :, :] = SLAP_ROI[z, :, :] + oneSeg

            if len(endpoints)>1:
                points = np.where(plane==1)
                points  = list(zip(points[1], points[0]))
                points =  DouglasPeucker(points, 1)
                pointArray = np.array(points)
                sortedPoints = np.zeros_like(pointArray)
                kdTree = KDTree(pointArray)
                for i, c in enumerate(kdTree.query([0,0], k=pointArray.shape[0])[1]):
                    sortedPoints[i, : ] = pointArray[c, :]

                for v in range(sortedPoints.shape[0]-1):
                    block, _ =  segmentGen(sortedPoints[v,:], sortedPoints[v+1,:], dendrites[z, :, :])
                    flipped =block
                    oneSeg = flipped*dendrites[z, :, :]
                    oneSeg = dilation(oneSeg)
                    flipped[flipped >0]= roi_ID
                    oneSeg[oneSeg >0]= roi_ID
                    roi_ID += 1
                    SLAP_Blocks[z, :, :] = SLAP_Blocks[z, :, :] + flipped
                    SLAP_ROI[z, :, :] = SLAP_ROI[z, :, :] + oneSeg

    soma = labels[0,:,:,:].copy()
    soma[labels[0,:,:,:]!=1]=0
    soma = np.array(soma, bool)


    mask_int = soma.astype(int)  

    # Use the largest group of pixels as the soma
    labeled_array = label(mask_int, connectivity=soma.ndim)
    regions = regionprops(labeled_array)
    largest_region = max(regions, key=lambda r: r.area)
    largest_component = (labeled_array == largest_region.label)

    soma2 = (labeled_array == largest_region.label)
    SOMA_POINT = center_of_mass(soma2)
    soma2[int(SOMA_POINT[0]),:,:].astype(int)



    SLAP_ROI[int(SOMA_POINT[0]),:,:]=soma2[int(SOMA_POINT[0]),:,:]                    
    SLAP_ROI = SLAP_ROI.astype(int)   
    SLAP_Blocks = SLAP_Blocks.astype(int)

    np.save("test.npy", SLAP_ROI)
    end = time.time()
    print('Time Elapsed: ', end - start)
    test = napari.Viewer()
    test.add_image(data1[:, 0, 0, :, :], name='Neuron', scale=(5, 1, 1), colormap='gray', blending='additive')
    #test.add_labels(segsperplane, name='Segments', scale=(5, 1, 1), blending='additive')
    test.add_labels(SLAP_ROI, name='ROI', scale=(5, 1, 1), blending='additive')
    #savemat("SatRoiWin%s.mat" %(str(win)), {'roi':roi})