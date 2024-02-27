import skimage as ski
import sys
def xyzshift(path1,path2):

    imstack1 = ski.io.imread(path1,plugin="tifffile")

    imstack2 = ski.io.imread(path2,plugin="tifffile")


    x = ski.registration.phase_cross_correlation(imstack1[0], imstack2[0], upsample_factor=1, space='real', disambiguate=False,
                                                 reference_mask=None, moving_mask=None,
                                                 overlap_ratio=0.3, normalization='phase')

    print(x[0][0], x[0][1], x[0][2])
    return x[0]
def main():
    if len(sys.argv)<2:
        print('No path to tif file given')
        sys.exit(1)
    Path1 = sys.argv[1]

    # Weird bug, unsure if this will occur on other comp
    Path1 = Path1[:-2]

    Path2 = sys.argv[4]
    xyzshift(Path1,Path2)

if __name__ == "__main__":
    main()