import sys
import subprocess
import os
import numpy as np


from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QLineEdit, QLabel
from PyQt5.QtWidgets import QComboBox, QPushButton

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
GUI_PATH = os.path.join(SCAM_PATH, "GUI")
RS_PATH = os.path.join(SCAM_PATH,'rs_motor')

sys.path.insert(1,RS_PATH)
from ESP32_light_utils import initialize_connection, move_to_esp32

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera & Spectrometer GUI")
        self.setGeometry(100, 100, 1200, 800)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        # Left panel
        left_panel = QVBoxLayout()
        self.btn_cam_roi = QPushButton("cam_roi")
        self.btn_scan_spec = QPushButton("scan spec")
        self.btn_cam_roi.clicked.connect(self.run_cam_roi)
        self.btn_scan_spec.clicked.connect(self.run_scan_spec)
        left_panel.addWidget(self.btn_cam_roi)
        left_panel.addWidget(self.btn_scan_spec)

        self.integration_label = QLabel("Integration Time (ms):")
        self.integration_input = QLineEdit()
        self.integration_input.setPlaceholderText("100")
        left_panel.addWidget(self.integration_label)
        left_panel.addWidget(self.integration_input)
        
        # Dropdowns for pan and tilt
        self.pan_dropdown = QComboBox()
        self.pan_dropdown.addItems([str(i) for i in range(90, -91, -1)])  # 90 to -90
        self.pan_label = QLabel("Horizontal (pan)")

        self.tilt_dropdown = QComboBox()
        self.tilt_dropdown.addItems([str(i) for i in range(36, -55, -1)])  # 36 to -54
        self.tilt_label = QLabel("Vertical (tilt)")

        self.btn_send_coords = QPushButton("Send")
        self.btn_send_coords.clicked.connect(self.send_coordinates)

        left_panel.addWidget(self.pan_label)
        left_panel.addWidget(self.pan_dropdown)
        left_panel.addWidget(self.tilt_label)
        left_panel.addWidget(self.tilt_dropdown)
        left_panel.addWidget(self.btn_send_coords)

        left_panel.addStretch()  # Move to the end

        layout.addLayout(left_panel, 1)


        # Right panel
        right_panel = QVBoxLayout()

        # Top half: images
        top_right_panel = QHBoxLayout()
        self.label_cam0 = QLabel("cam0")
        self.label_cam1 = QLabel("cam1")
        self.label_cam0.setAlignment(Qt.AlignCenter)
        self.label_cam1.setAlignment(Qt.AlignCenter)
        top_right_panel.addWidget(self.label_cam0)
        top_right_panel.addWidget(self.label_cam1)
        right_panel.addLayout(top_right_panel, 2)

        # Bottom half: plot
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        right_panel.addWidget(self.canvas, 1)

        layout.addLayout(right_panel, 3)

    def run_cam_roi(self):
        cam0_path = os.path.join(CAM_ROI_PATH, "roi_cam0.jpg")
        cam1_path = os.path.join(CAM_ROI_PATH, "roi_cam1.jpg")
        if os.path.exists(cam0_path) and os.path.exists(cam1_path):
            print("EXIST!")
            self.load_images()
        else:
            subprocess.run(["python3", os.path.join(CAM_ROI_PATH, "roi_master_script.py")])
            self.load_images()

    def run_scan_spec(self):
        int_time = self.integration_input.text()
        if int_time.strip() == "":
            int_time = "100"
        subprocess.run(["python3", os.path.join(SPEC_SCAN_PATH, "simple_scan.py"), int_time])
        self.load_plot()

    def load_images(self):
        print('load images')
        for idx, label in enumerate([self.label_cam0, self.label_cam1]):
            fname = os.path.join(CAM_ROI_PATH, f"roi_cam{idx}.jpg")
            print(fname)
            if os.path.exists(fname):
                pixmap = QPixmap(fname).scaled(400, 300, Qt.KeepAspectRatio)
                label.setPixmap(pixmap)
            else:
                label.setText(f"{fname} not found")
    
    def load_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        try:
            data = np.load(os.path.join(GUI_PATH, "scan_output.npz"))
            wavelengths = data["wavelength"]
            intensity = data["dark_avg"]
            ax.plot(wavelengths, intensity)
            ax.set_title("Spectrometer Output")
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity")
        except Exception as e:
            ax.text(0.5, 0.5, f"Error loading spectrum:\n{str(e)}", ha='center', va='center')
        self.canvas.draw()
    
    def send_coordinates(self):
        try:
            pan = int(self.pan_dropdown.currentText())
            tilt = int(self.tilt_dropdown.currentText())
            initialize_connection()
            move_to_esp32(pan, tilt)
        except Exception as e:
            print(f"Error sending coordinates: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
