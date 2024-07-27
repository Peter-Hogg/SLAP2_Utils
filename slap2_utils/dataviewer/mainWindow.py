from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QLabel, QHBoxLayout, QLineEdit
from PyQt6.QtCore import Qt
import sys
import os

from pixelTraces import tracePixelSelector
 



class FileSelector(QWidget):
    def __init__(self, label_text, file_filter):
        super().__init__()
        self.layout = QHBoxLayout()
        self.label = QLabel(label_text)
        self.button = QPushButton("Browse")
        self.file_filter = file_filter
        self.button.clicked.connect(self.browse_file)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.filepath = 'No file selected'

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_name:
            self.label.setText(os.path.basename(file_name))
        self.filepath = file_name
    def get_selected_file(self):
        return self.filepath

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Slap2 Data Viewer")

        self.DataFilePath = FileSelector("No file selected (Binary)", "SLAP2 Binary (*.dat)")
        self.StackPath = FileSelector("No file selected (Stack)", "Stack (*.tif)")
        self.StimPath = FileSelector("No Stim Log", "Stimlog (*.h5)")

        self.run_button = QPushButton("Run Scripts")
        self.run_button.clicked.connect(self.viewSuperPixelTraces)

        layout = QVBoxLayout()
        layout.addWidget(self.DataFilePath)
        layout.addWidget(self.StackPath)
        layout.addWidget(self.StimPath)
        layout.addWidget(self.run_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStyleSheet("QPushButton { color: black; }")

    def viewSuperPixelTraces(self):
        datFile = self.DataFilePath.get_selected_file()
        stim = self.StimPath.get_selected_file()
        print(datFile)
        if datFile.startswith("No file selected"):
            print("Please select all files before launching the second window.")
            return
        if stim.startswith("No file selected"):
            stim = None
        
        print('SuperPixViwer')
        # Launch the second window with the selected file paths
        self.superPixSel = tracePixelSelector([datFile, stim])
        self.superPixSel.show()



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())