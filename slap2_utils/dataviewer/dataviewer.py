from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QCoreApplication
from skimage.draw import polygon_perimeter

import fastplotlib as fpl
import numpy as np

from ..datafile import DataFile

def viewROItraces(ch=1, zIdz=1, windowWidth_lines=10, expectedWindowWidth_lines = 100):
    # Values or trace
    mask = np.full((800, 1280), True, dtype=bool)
    rasterPixels = mask
    integrationPixels = mask
    
    # QT file picker    
    app = QtWidgets.QApplication([])
    fileName = QtWidgets.QFileDialog.getOpenFileName(None,
        QCoreApplication.translate("MainWindow", "Open Data File"),
        QCoreApplication.translate("MainWindow", "Data Files (*.dat)"))[0]
    
    
    # Load Data
    experiment = DataFile(fileName)
    rois2D = return2Droi(experiment)

    plot = fpl.Plot(canvas="qt")
    plot.add_image(rois2D)
    plot.camera.local.scale *= -1
    plot.show()
    plot.canvas.resize(*rois2D.shape[:2])


    def autoscale(ev):
        if ev.key == "r":
            plot.auto_scale()


    # useful if you pan/zoom away from the image
    plot.renderer.add_event_handler(autoscale, "key_down")

    # execute Qt app
    app.exec()



def return2Droi(datafile):
    img = np.zeros((800, 1280), dtype=np.uint8)

    for _roi in range(len(datafile.metaData.AcquisitionContainer.ROIs)):
        roi_shape = datafile.metaData.AcquisitionContainer.ROIs[_roi].shapeData
        
        rr, cc = polygon_perimeter(roi_shape[0,:],
                                    roi_shape[1,:],
                                    shape=img.shape, clip=True)

        img[rr, cc] = _roi+1

    return(img)

def returnTraces(datafile):
    zIdx = 1
    chIdx = 1
hTrace = Trace(hDataFile,zIdx,chIdx);


from skimage.draw import polygon_perimeter

roi_shape = hDataFile.metaData.AcquisitionContainer.ROIs[0].shapeData

img = np.zeros((800, 1280), dtype=np.uint8)

rr, cc = polygon_perimeter(roi_shape[0,:], roi_shape[1,:],

                           shape=img.shape, clip=True)

img[rr, cc] = 1

plt.imshow(img)

#rasterPixels = pixelMask;
#integrationPixels = pixelMask;

pixelMask=np.full((800, 1280), False)
pixelMask[img==1] = True

rasterPixels = np.full((800, 1280), False)
integrationPixels = pixelMask;

hTrace.setPixelIdxs(rasterPixels, integrationPixels);
#windowWidth_lines = 10;
#expectedWindowWidth_lines = 100;
#trace = hTrace.process(windowWidth_lines,expectedWindowWidth_lines);
_trace, _, _, _ = hTrace.process(10, 100)
print(_trace)
plt.plot(_trace)


viewROItraces()
