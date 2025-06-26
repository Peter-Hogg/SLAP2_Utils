import sys
import numpy as np
from vispy import app
app.use_app('pyqt6')
from vispy import scene
from vispy.color import Colormap
from vispy.scene import visuals
from matplotlib import cm
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

class VolumeViewer(QMainWindow):
    def __init__(self, volume_data, roi_data):
        super().__init__()

        self.setWindowTitle("3D Volume and ROI Viewer")

        # Create a Vispy canvas
        canvas = scene.SceneCanvas(keys='interactive', show=True)
        view = canvas.central_widget.add_view()

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

    # Create synthetic data for demonstration
    volume_data = np.random.rand(100, 100, 100).astype(np.float32)
    volume_data = np.clip(volume_data * 255, 0, 255)  # Scale to 0-255

    # Create synthetic ROI data with 5 ROIs
    roi_data = np.zeros_like(volume_data)
    roi_data[20:40, 20:40, 20:40] = 1
    roi_data[50:70, 50:70, 50:70] = 2
    roi_data[30:50, 30:50, 10:30] = 3
    roi_data[60:80, 10:30, 40:60] = 4
    roi_data[40:60, 60:80, 60:80] = 5

    # Create and show the main window
    window = VolumeViewer(volume_data, roi_data)
    window.show()

    # Start the Qt event loop
    sys.exit(app.exec())