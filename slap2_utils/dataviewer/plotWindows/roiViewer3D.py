import sys
import numpy as np
from vispy import scene
from vispy.color import Colormap
from vispy.scene import visuals
from matplotlib import cm
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from slap2_utils.utils.roi_utils import roiLabels


class ROIViewer3D(QMainWindow):
    def __init__(self, img_path, hdatafile):
        super().__init__()

        self.setWindowTitle("3D ROI Viewer")
        
        # Load the image stack if provided
        self.img = tifffile.imread(img_path) if img_path is not None else None

        # Generate ROI labels
        self.labels = roiLabels(hdatafile, img_path)

        # Set up the main layout
        layout = QVBoxLayout()

        # Create a Napari viewer

        if self.img is not None:
            volume_data = self.img

        #self.viewer.add_labels(self.labels, name="ROI Labels")


        # Create a grayscale colormap for the volume
        grayscale_cmap = Colormap([(0, 0, 0, 0), (1, 1, 1, 1)])

        # Add the volume with the grayscale colormap
        volume = visuals.Volume(volume_data, parent=view.scene, threshold=0.225,
                                cmap=grayscale_cmap, clim=[np.min(volume_data), np.max(volume_data)])

        # Add ROI as separate isosurfaces, each with a different color from the spectral colormap
        unique_labels = np.unique(roi_data)
        spectral_cmap = cm.get_cmap('Spectral', len(unique_labels))

        for i, label in enumerate(unique_labels):
            if label == 0:
                continue  # Skip background
            mask = (roi_data == label).astype(np.float32)
            color = spectral_cmap(i)[:3]  # Get RGB color from colormap
            iso = visuals.Isosurface(mask, level=0.5, color=color + (0.5,), parent=view.scene)

        # Set the camera to view the volume
        view.camera = scene.cameras.TurntableCamera(fov=60, azimuth=180)

        # Embed the Vispy canvas into the Qt layout
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        layout.addWidget(canvas.native)
        self.setCentralWidget(widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print(app)

    window = ROIViewer3D()

    # Start the Qt event loop
    sys.exit(app.exec())