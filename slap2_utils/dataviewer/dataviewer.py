from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QCoreApplication
import fastplotlib as fpl
import numpy as np

from ..file.datafile import DataFile

def viewROItraces(ch=1, zIdz=1, windowWidth_lines=10, expectedWindowWidth_lines = 100):
    # Values or trace
    mask = np.full((800, 1280), True, dtype=bool)
    rasterPixels = mask
    integrationPixels = mask
    
    # QT file picker    
    app = QtWidgets.QApplication([])
    fileName = QtWidgets.QFileDialog.getOpenFileName(None,
    QCoreApplication.translate("MainWindow", "Open Data File"),  QCoreApplication.translate("MainWindow", "Data Files (*.dat)"))

    # Load Data
    experiment = DataFile(fileName)
    rois2D = returnROIplot(experiment)

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


viewROItraces()



def return2Droi(datafile):
    img = np.zeros((800, 1280), dtype=np.uint8)

    for _roi in len(datafile.metaData.AcquisitionContainer.ROIs[0]):
        roi_shape = exp1.metaData.AcquisitionContainer.ROIs[_roi].shapeData
        
        rr, cc = polygon_perimeter(roi_shape[0,:],
                                    roi_shape[1,:],
                                    shape=img.shape, clip=True)

        img[rr, cc] = _roi+1

    return(img)