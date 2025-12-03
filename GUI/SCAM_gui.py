import datetime
from datetime import datetime, timedelta
import sys
import subprocess
import os
import numpy as np
import time
from data_handler import ScanDataHandler  # Import the new data handler

from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QPushButton

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
DATA_PATH = os.path.join(SCAM_PATH, "data")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
GUI_PATH = os.path.join(SCAM_PATH, "GUI")
RS_PATH = os.path.join(SCAM_PATH,'rs_motor')

sys.path.insert(1,RS_PATH)
from ESP32_light_utils import initialize_connection, move_to_esp32

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.auto_scam_active = False
        self.auto_scam_end_time = None
        self.photo_timer = QTimer()
        self.scan_timer = QTimer()
        self.data_handler = ScanDataHandler()  # Initialize data handler
        self.setWindowTitle("SCAM")
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
        
        # Camera shutter time inputs
        self.label_shutter0 = QLabel("Shutter time cam0 (μs):")
        self.input_shutter0 = QLineEdit()
        self.input_shutter0.setPlaceholderText("100000")

        self.label_shutter1 = QLabel("Shutter time cam1 (μs):")
        self.input_shutter1 = QLineEdit()
        self.input_shutter1.setPlaceholderText("1000000")

        self.btn_take_photo = QPushButton("Take Photo")
        self.btn_take_photo.clicked.connect(self.take_photo)

        left_panel.addWidget(self.label_shutter0)
        left_panel.addWidget(self.input_shutter0)
        left_panel.addWidget(self.label_shutter1)
        left_panel.addWidget(self.input_shutter1)
        left_panel.addWidget(self.btn_take_photo)
        
        # Interval input
        self.label_interval = QLabel("Interval (minutes):")
        self.input_interval = QLineEdit()
        self.input_interval.setPlaceholderText("30")

        # Twitch coordinates
        self.label_twitch_up = QLabel("Twitch Up (x,y):")
        self.input_twitch_up = QLineEdit()
        self.input_twitch_up.setPlaceholderText("0,10")

        self.label_twitch_down = QLabel("Twitch Down (x,y):")
        self.input_twitch_down = QLineEdit()
        self.input_twitch_down.setPlaceholderText("0,-10")

        # Auto SCAM button
        self.btn_auto_scam = QPushButton("Auto SCAM Start")
        self.btn_auto_scam.clicked.connect(self.start_auto_scam)

        
        self.label_duration = QLabel("Run For (minutes):")
        self.input_duration = QLineEdit()
        self.input_duration.setPlaceholderText("480")  # 8 hours default
        
        self.btn_stop_auto_scam = QPushButton("Stop Auto SCAM")
        self.btn_stop_auto_scam.clicked.connect(self.stop_auto_scam)
        self.btn_stop_auto_scam.setEnabled(False)
        
        self.label_status = QLabel("Auto SCAM: Inactive")
        # Add to left panel
        left_panel.addWidget(self.label_interval)
        left_panel.addWidget(self.input_interval)
        left_panel.addWidget(self.label_twitch_up)
        left_panel.addWidget(self.input_twitch_up)
        left_panel.addWidget(self.label_twitch_down)
        left_panel.addWidget(self.input_twitch_down)
        left_panel.addWidget(self.btn_auto_scam)

        left_panel.addWidget(self.label_duration)
        left_panel.addWidget(self.input_duration)
        left_panel.addWidget(self.btn_stop_auto_scam)
        left_panel.addWidget(self.label_status)


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
            self.load_images(cam0_path, cam1_path)
        else:
            subprocess.run(["python3", os.path.join(CAM_ROI_PATH, "roi_master_script.py")])
            self.load_images(cam0_path, cam1_path)

    def run_scan_spec(self):
        int_time = self.integration_input.text()
        if int_time.strip() == "":
            int_time = "100"
        subprocess.run(["python3", os.path.join(SPEC_SCAN_PATH, "simple_scan.py"), int_time])
        self.load_plot()
    

    def start_auto_scam(self):
        if self.auto_scam_active:
            QMessageBox.information(self, "Info", "Auto SCAM is already running")
            return

        try:
            # Get all parameters
            photo_interval_minutes = int(self.input_interval.text().strip() or "30")
            twitch_up = tuple(map(int, (self.input_twitch_up.text().strip() or "0,10").split(',')))
            twitch_down = tuple(map(int, (self.input_twitch_down.text().strip() or "0,-10").split(',')))
            shutter0 = self.input_shutter0.text().strip() or "100000"
            shutter1 = self.input_shutter1.text().strip() or "1000000"
            
            # Get time parameters
            duration_minutes = int(self.input_duration.text().strip() or "480")
            
            self.auto_scam_end_time = datetime.now() + timedelta(minutes=duration_minutes)
            
            # Initialize connection
            initialize_connection()
            move_to_esp32(0, 0)
            
            # Set up status
            self.auto_scam_active = True
            self.btn_auto_scam.setEnabled(False)
            self.btn_stop_auto_scam.setEnabled(True)
            self.update_status()
            
            # Set up timers
            self.photo_timer.timeout.connect(lambda: self.take_photos_sequence(twitch_up, twitch_down, shutter0, shutter1))
            self.photo_timer.start(photo_interval_minutes * 60 * 1000)  # Convert to milliseconds
            
            # Start scan sequence immediately
            self.run_scan_sequence(twitch_up, twitch_down)
            
            # Run first photo sequence immediately
            self.take_photos_sequence(twitch_up, twitch_down, shutter0, shutter1)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto SCAM initialization failed: {str(e)}")
            self.stop_auto_scam()
    def run_scan_sequence(self, twitch_up, twitch_down):
        """Run the spectrometer scan sequence (5 scans up, 5 scans down)"""
        if not self.auto_scam_active:
            return
            
        try:
            # Move up and scan 5 times
            move_to_esp32(*twitch_up)
            self.update_status("Scanning up position...")
            for _ in range(5):
                if not self.auto_scam_active:
                    return
                self.run_single_scan(twitch_up)
                time.sleep(2)  # 2 second break between scans
                
            # Move down and scan 5 times
            move_to_esp32(*twitch_down)
            self.update_status("Scanning down position...")
            for _ in range(5):
                if not self.auto_scam_active:
                    return
                self.run_single_scan(twitch_down)
                time.sleep(2)  # 2 second break between scans
                
            # Schedule next scan sequence in 1 minute (or adjust as needed)
            self.scan_timer.singleShot(60000, lambda: self.run_scan_sequence(twitch_up, twitch_down))
            
        except Exception as e:
            self.update_status(f"Scan error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Scan sequence failed: {str(e)}")

    def run_single_scan(self, coordinates):
        """Run a single spectrometer scan and store the data"""
        int_time = self.integration_input.text().strip() or "100"
        try:
            subprocess.run(["python3", os.path.join(SPEC_SCAN_PATH, "simple_scan.py"), int_time])
            
            # Load and store the scan data
            data = np.load(os.path.join(GUI_PATH, "scan_output.npz"))
            wavelengths = data["wavelength"]
            intensity = data["dark_avg"]
            
            # Store in data handler
            self.data_handler.add_scan(coordinates, wavelengths, intensity)
            
            # Update plot
            self.load_plot()
            
        except Exception as e:
            raise Exception(f"Spectrometer scan failed: {str(e)}")

    def take_photos_sequence(self, twitch_up, twitch_down, shutter0, shutter1):
        """Take photos in both positions"""
        if not self.auto_scam_active:
            return
            
        try:
            # Move up and take photo
            move_to_esp32(*twitch_up)
            self.update_status("Taking photo up...")
            self.take_photo()
            self.data_handler.add_photo_time(time.time())
            
            # Move down and take photo
            move_to_esp32(*twitch_down)
            self.update_status("Taking photo down...")
            self.take_photo()
            self.data_handler.add_photo_time(time.time())
            
        except Exception as e:
            self.update_status(f"Photo error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Photo sequence failed: {str(e)}")

    def stop_auto_scam(self):
        if hasattr(self, 'auto_scam_timer'):
            self.auto_scam_timer.stop()
        self.auto_scam_active = False
        self.btn_auto_scam.setEnabled(True)
        self.btn_stop_auto_scam.setEnabled(False)
        self.update_status()
    def auto_scam_iteration(self, twitch_up, twitch_down, shutter0, shutter1):

        if not self.auto_scam_active:
            return
        
        # Check if we should stop
        if datetime.now() >= self.auto_scam_end_time:
            self.stop_auto_scam()
            QMessageBox.information(self, "Info", "Auto SCAM completed scheduled duration")
            return
            
        try:
            self.update_status("Running scan...")
            
            # Take photo
            self.take_photo()
            
            # Run spec scan
            self.run_scan_spec()
            
            # Twitch movement with visual feedback
            if hasattr(self, 'last_twitch_up'):
                move_to_esp32(*twitch_down)
                self.last_twitch_up = False
                self.update_status("Moving down...")
            else:
                move_to_esp32(*twitch_up)
                self.last_twitch_up = True
                self.update_status("Moving up...")
                
            # Update status with next run time
            next_run = datetime.now() + timedelta(
                minutes=int(self.input_interval.text().strip() or "30"))
            self.update_status(f"Next run at {next_run.strftime('%H:%M')}")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Auto SCAM iteration failed: {str(e)}")

    def update_status(self, message=None):
        if message:
            status = f"Auto SCAM: {message}"
        elif self.auto_scam_active:
            remaining = self.auto_scam_end_time - datetime.now()
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes = remainder // 60
            status = f"Auto SCAM: Active ({hours}h {minutes}m remaining)"
        else:
            status = "Auto SCAM: Inactive"
            
        self.label_status.setText(status)
        
    def load_images(self, path0=os.path.join(CAM_ROI_PATH,"roi_cam0.jpg"), path1=os.path.join(CAM_ROI_PATH,"roi_cam1.jpg")):
        for idx, (label, path) in enumerate(zip([self.label_cam0, self.label_cam1], [path0, path1])):
            if os.path.exists(path):
                pixmap = QPixmap(path).scaled(400, 300, Qt.KeepAspectRatio)
                label.setPixmap(pixmap)
            else:
                label.setText(f"{path} not found")
    
    def take_photo(self):
        shutter0 = self.input_shutter0.text().strip() or "100000"
        shutter1 = self.input_shutter1.text().strip() or "1000000"
        try:
            subprocess.run(
                ["/bin/bash",os.path.join(CAM_ROI_PATH,'cam_take_photo.sh'), shutter0, shutter1],
                check=True
            )
            self.load_images(os.path.join(CAM_ROI_PATH,"cam0_0.jpg"), os.path.join(CAM_ROI_PATH,"cam1_0.jpg"))
        except subprocess.CalledProcessError as e:
            print(f"Photo capture failed: {e}")

    
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
