import skimage as ski
import sys

import pandas as pd

def xyzshift_UI(path1,slice,image):

    imstack1 = ski.io.imread(path1,plugin="tifffile")

    # See which one has the least error and shift from there
    besterror = 1000000000000000000000000000000
    bestindex = -100

    shift = []

    for i in range(len(imstack1[0])):
        result = ski.registration.phase_cross_correlation(imstack1[0][i], image, upsample_factor=100, space='real', disambiguate=False,
                                                     reference_mask=None, moving_mask=None,
                                                     normalization=None)
        if result[1] < besterror:
            besterror = result[1]
            bestindex = i
            shift = result[0]
    z_change = (i+1) - int(slice[0])
    print(z_change, shift[0], shift[1])

def main():
    # Loading bunch of stuff

    if len(sys.argv)<2:
        print('No path to tif file given')
        sys.exit(1)

    Path1 = sys.argv[1]

    Slice = sys.argv[2]

    I = sys.argv[3]

    image = pd.read_csv(I,header=None)



    xyzshift_UI(Path1,Slice,image)

if __name__ == "__main__":
    main()