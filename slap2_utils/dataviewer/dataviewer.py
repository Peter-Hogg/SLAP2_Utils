from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QCoreApplication
from skimage.draw import polygon_perimeter

import fastplotlib as fpl
import numpy as np

from ..datafile import DataFile
from ..utils.trace import Trace





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




# Qt app MUST be instantiated before creating any fpl objects, or any other Qt objects
app = QtWidgets.QApplication([])

# QT file picker    
fileName = QtWidgets.QFileDialog.getOpenFileName(None,
    QCoreApplication.translate("MainWindow", "Open Data File"),
    QCoreApplication.translate("MainWindow", "Data Files (*.dat)"))[0]

exp1 = DataFile(fileName)
zIdx = 1
chIdx = 1 
hTrace = Trace(exp1,zIdx,chIdx)

windowWidth_lines = 5
expectedWindowWidth_lines = 100
roi_shape = exp1.metaData.AcquisitionContainer.ROIs[0].shapeData
img = np.zeros((800, 1280), dtype=np.uint8)

rr, cc = polygon_perimeter(roi_shape[0,:],
                           roi_shape[1,:],

                           shape=img.shape, clip=True)

img[rr, cc] = 1
mask = np.full((800, 1280), False, dtype=bool)
mask[img==1]=True
rasterPixels = np.full((800, 1280), False, dtype=bool)
integrationPixels = mask

hTrace.setPixelIdxs(rasterPixels,integrationPixels)

_trace, _, _, _ = hTrace.process(windowWidth_lines, expectedWindowWidth_lines)

# force qt canvas, wgpu will sometimes pick glfw by default even if Qt is present
plot = fpl.Plot(canvas="qt")
dmdCanvas = np.zeros((800, 1280))
plot.add_image(np.zeros((800, 1280)), name="ROI_1")
#plot.camera.local.scale *= -1


def update_frame(ix):
    
    img = np.zeros((800, 1280), dtype=np.uint8)
    for _line , col in enumerate(list(np.unique(cc))):
        _superPixVal = hTrace.TracePixels[_line].data[0][int(ix)]
        print(_superPixVal)
        for _row in list(np.where(cc==col)[0]):
            img[rr[_row], col] = _superPixVal

    plot["ROI_1"].data = img
    # you can also do plot.graphics[0].data = video[ix]


# create a QMainWindow, set the plot canvas as the main widget
# The canvas does not have to be in a QMainWindow and it does
# not have to be the central widget, it will work like any QWidget
main_window = QtWidgets.QMainWindow()
main_window.setCentralWidget(plot.canvas)

# Create a QSlider for updating frames
slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
slider.setMaximum(hTrace.TracePixels[0].data[0][:].shape[0]-1)
slider.setMinimum(0)
slider.valueChanged.connect(update_frame)

# put slider in a dock
dock = QtWidgets.QDockWidget()
dock.setWidget(slider)

# put the dock in the main window
main_window.addDockWidget(
    QtCore.Qt.DockWidgetArea.BottomDockWidgetArea,
    dock
)

# calling plot.show() is required to start the rendering loop
plot.show()

# set window size from width and height of video
main_window.resize(dmdCanvas.shape[0], dmdCanvas.shape[1])

# show the main window
main_window.show()

# execute Qt app
app.exec()