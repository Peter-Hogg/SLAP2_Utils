from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pyneurotrace.gpu.filters as filters
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.cm as cm
import sys
from tifffile import imread
from slap2_utils.utils.roi_utils import roiLabels


def plotROI(ax, labels, stack, z, z_positions):
    ax.clear()

    # Plot the image stack if provided
    if stack is not None:
        ax.imshow(stack[z, :, :], cmap='gray')
    else:
        ax.imshow(np.zeros(labels[z, :, :].shape), cmap='gray')
    # Create contours from ROI labels and plot them
    # Normalize the labels to create a color map
    norm = mpl.colors.Normalize(vmin=1, vmax=np.max(labels))
    cmap = cm.Spectral

    # Create contours from ROI labels and color them based on integer values
    unique_labels = np.unique(labels[z, :, :])
    for i in unique_labels:
        if i == 0:
            continue  # Skip background
        mask = labels[z, :, :] == i
        color = cmap(norm(i))
        ax.contour(mask, levels=[0.5], colors=[color], linewidths=1)

        # Find the centroid of the mask to place the label
        if np.any(mask):
            y, x = np.mean(np.argwhere(mask), axis=0)
            ax.text(x, y, str(i), color='white', fontsize=8, ha='center', va='center', weight='bold')

    # Add Z-position text in the lower-left corner
    z_position_text = f"Z: {z_positions[z+1]:.2f} µm"  # Skip the first value in z_positions
    ax.text(0.02, 0.02, z_position_text, color='white', fontsize=10, ha='left', va='bottom', transform=ax.transAxes)


    ax.set_xticks([])
    ax.set_yticks([])
    ax.figure.canvas.draw()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)
        self.initialized = False

    def plot(self, labels, stack, z_positions):
        if not self.initialized:
            self.initialize_plot(labels, stack, z_positions)
        else:
            plotROI(self.ax,labels, stack)

    def initialize_plot(self, labels, stack, z_positions):
        _z =0
        plotROI(self.ax, labels, stack, _z, z_positions)
   
        self.ax.figure.canvas.draw()

    def update_plot(self, labels, stack, z, z_positions):
        plotROI(self.ax, labels, stack, z, z_positions)

class roiViewer(QMainWindow):
    def __init__(self, channel, hdatafile, imgPath):
        super().__init__()

        self.setWindowTitle(f"All ROI Traces")

        layout = QVBoxLayout()

        # Create a PlotCanvas instance
        self.canvas = PlotCanvas(self, width=24, height=16)
        layout.addWidget(self.canvas)
        if imgPath == None:
            self.img = None
        else:
            self.img = imread(imgPath)
        self.labels = roiLabels(hdatafile, imgPath)
        self.z_positions = hdatafile.fastZs[1:]
        self.canvas.plot(self.labels, self.img, self.z_positions)

        # Create a QSlider for updating frames
        if imgPath == None:
            if len(hdatafile.fastZs) > 2:
            
                self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
                self.slider.setMaximum(len(hdatafile.fastZs))
                self.slider.setMinimum(0)
                self.slider.valueChanged.connect(self.update_frame)
                layout.addWidget(self.slider)

        else:
            print(self.img.shape)
            z = self.img.shape[1]
            if z > 1:
                self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
                self.slider.setMaximum(z - 1)
                self.slider.setMinimum(0)
                self.slider.valueChanged.connect(self.update_frame)
                layout.addWidget(self.slider)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    def update_frame(self, z):
        self.canvas.update_plot(self.labels, self.img, z, self.z_positions)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = superPixelPlot(roi_index=0, channel=1, hdatafile=None, stim_times=None)
    window.show()
    sys.exit(app.exec())