import sys
import tifffile
from slap2_utils.utils.roi_utils import roiLabels
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
import napari

class ROIViewer3D(QMainWindow):
    def __init__(self, img_path, hdatafile):
        super().__init__()

        self.setWindowTitle("3D ROI Viewer")
        
        # Load the image stack if provided
        self.img = tifffile.imread(img_path) if img_path is not None else None

        # Generate ROI labels
        self.labels = roiLabels(hdatafile, img_path)

        # Get z positions excluding the first (invalid) value
        # Set up the main layout
        layout = QVBoxLayout()

        # Create a Napari viewer
        self.viewer = napari.Viewer()
        self.viewer.dims.ndisplay = 3
        if self.img != None:
            self.viewer.add_image(self.img)

        self.viewer.add_labels(self.labels, name="ROI Labels", color={i: cmap for i, cmap in enumerate(plt.cm.Spectral.colors)})
        self.viewer.window._qt_viewer.dockLayerControls.close()
        self.viewer.window._qt_viewer.dockLayerList.close()

        # Embed the Napari viewer in a QWidget
        viewer_container = QWidget()
        viewer_container.setLayout(QVBoxLayout())
        viewer_container.layout().addWidget(self.viewer.window._qt_window)

        # Add the Napari viewer to the main layout
        layout.addWidget(viewer_container)
        # Create a toggle button
        self.toggle_button = QPushButton("Toggle 2D/3D")
        self.toggle_button.clicked.connect(self.toggle_display_mode)
        layout.addWidget(self.toggle_button)

        # Set the central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_display_mode(self):
        # Toggle between 2D (ndisplay=2) and 3D (ndisplay=3) modes
        if self.viewer.dims.ndisplay == 3:
            self.viewer.dims.ndisplay = 2
        else:
            self.viewer.dims.ndisplay = 3

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the main window
    window = ROIViewer3D()
    window.show()

    # Start the Qt event loop
    sys.exit(app.exec())