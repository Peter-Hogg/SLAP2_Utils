from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton, QRadioButton, QButtonGroup, QHBoxLayout
from PyQt6.QtCore import Qt
import sys

from slap2_utils.datafile import DataFile
from slap2_utils.functions import stim

from plotWindows.superPixPlot import superPixelPlot

class tracePixelSelector(QMainWindow):
    def __init__(self, file_paths):
        super().__init__()

        self.setWindowTitle("Super Pixel Plotting")
        self.hDataFile = DataFile(file_paths[0])
        print(self.hDataFile.metaDataFileName)
        if file_paths[1] is not None:
            self.stimTimes = stim.returnStimTime(file_paths[1]) 
        else:
            self.stimTimes = None

        layout = QVBoxLayout()
        
        # Create dropdown selector
        self.dropdown = QComboBox()
        roiIndices = [str(i) for i in range(len(self.hDataFile.metaData.AcquisitionContainer.ROIs))]
        self.dropdown.addItems(roiIndices)

        self.radio_button_1 = QRadioButton("Channel 1")
        self.radio_button_2 = QRadioButton("Channel 2")
        self.radio_button_1.setChecked(True)  # Default selection

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_button_1, 1)
        self.button_group.addButton(self.radio_button_2, 2)

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.radio_button_1)
        radio_layout.addWidget(self.radio_button_2)
        
        layout.addLayout(radio_layout)
        layout.addWidget(QLabel("Select a ROI:"))
        layout.addWidget(self.dropdown)

        # Add a button to open the PlotWindow
        self.plot_button = QPushButton("Plot ROI Data")
        self.plot_button.clicked.connect(self.open_plot_window)
        layout.addWidget(self.plot_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStyleSheet("QPushButton { color: black; }")

    def open_plot_window(self):
        selected_roi = int(self.dropdown.currentText())
        selected_channel = self.button_group.checkedId() 
        self.plot_window = superPixelPlot(selected_roi, selected_channel, self.hDataFile)
        self.plot_window.show()