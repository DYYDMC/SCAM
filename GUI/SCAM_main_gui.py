import numpy as np
import glob
import matplotlib.pyplot as plt
import io
import time
import subprocess
import sys
import os
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow,QGraphicsScene
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtUiTools import loadUiType

# Add matplotlib integration
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Load the .ui file directly
Ui_MainWindow, QtBaseClass = loadUiType('/home/ydeng/Github/SCAM/GUI/SCAM_gui.ui')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(project_root)

# load SCAN-related functions
from spec_scan.spectrometer_controller import SpectrometerController
# from rs_motor.rcmotor_controller import MotorController
from stepper.OS_end.steppers import StepperController

# define paths
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CHESS_PATH = os.path.join(SCAM_PATH, "spherical")
ROI_PATH = os.path.join(SCAM_PATH, "roi")
DATA_PATH = os.path.join(SCAM_PATH, "data")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
CALI_PATH = os.path.join(SCAM_PATH,"cali")
SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
GUI_PATH = os.path.join(SCAM_PATH, "GUI")
GUI_CAM0 = os.path.join(GUI_PATH,'cam0')
GUI_CAM1 = os.path.join(GUI_PATH,'cam1')
STP_PATH =os.path.join(SCAM_PATH,'stepper')
# SPEC_ROI_CAM_POS=[(0,1),(10,1),(2,1),(10,4),(4,1),(10,0),(1,-4),(10,4)]
#SPEC_ROI_CAM_POS=[(0,0),(0,-10),(0,-20)]
SPEC_TILT_POS=[18,13,8,3,-2,-7,-12,-18]

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # Set window icon programmatically
        icon_path = os.path.join(os.path.dirname(__file__), 'SCAM_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")
        
        ## instantiate the SpectrometerController and MotorController
        self.spec_controller = SpectrometerController()
        self.stepper_controller = StepperController()
        
        # Replace QGraphicsView with matplotlib FigureCanvas
        self.spectrum_figure = Figure(figsize=(5, 3))
        self.spectrum_canvas = FigureCanvas(self.spectrum_figure)
        
        # Replace the QGraphicsView in the layout
        layout = self.verticalLayout_scan_oneScan
        # Remove the QGraphicsView and add matplotlib canvas
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget == self.graphicsView_scan_oneScan:
                layout.removeWidget(widget)
                widget.deleteLater()
                break
        
        # Add the matplotlib canvas to the layout
        layout.addWidget(self.spectrum_canvas)
        
        self.connect_signals()
        
    def connect_signals(self):
        """Connect all UI buttons to their functions"""
        
        # OneScan section
        self.btn_spec_scan.clicked.connect(self.on_spec_scan)
        self.btn_spec_move.clicked.connect(self.on_move_scan)
        self.btn_spec_reset.clicked.connect(self.on_reset_pos)
        self.btn_measure_dark.clicked.connect(self.on_measure_dark)
        
        # Camera section
        self.btn_green_shoot.clicked.connect(self.on_green_shoot)
        self.btn_uv_shoot.clicked.connect(self.on_uv_shoot)
        self.btn_both_shoot.clicked.connect(self.on_both_shoot)
        
        # SCAM
        self.btn_update.clicked.connect(self.on_update_parameters)
        self.btn_start_scam.clicked.connect(self.on_start_scam)
        self.btn_green_pano.clicked.connect(self.on_green_pano)
    
    def load_plot(self):
        """Simple load_plot function similar to your original"""
        self.spectrum_figure.clear()
        ax = self.spectrum_figure.add_subplot(111)
        try:
            GUI_PATH = os.path.join(project_root, "GUI")
            data = np.load(os.path.join(GUI_PATH, "scan_output.npz"))
            wavelengths = data["wavelength"]
            intensity = data["dark_avg"]
            ax.plot(wavelengths, intensity)
            #ax.set_title("Spectrometer Output")
            ax.set_xlabel("Wavelength (nm)")
            #ax.set_ylabel("Intensity")
            ax.grid(True, alpha=0.3)
        except Exception as e:
            ax.text(0.5, 0.5, f"Error loading spectrum:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
        
        self.spectrum_canvas.draw()
    # OneScan functions
    def on_measure_dark(self):
        self.int_t = self.spinBox_int_oneScan.value()
        self.isi = self.spinBox_isi_oneScan.value()
        for ii in range(10):
            # Perform scan
            result = self.spec_controller.scan(self.int_t)
            ints = result["intensity"]
            nms = result['wavelengths']
            print("Scan successful, saving data...")
            # Save data logic here
            data_filename = os.path.join(DATA_PATH, f"int_t{self.int_t}_darkNoise_no{ii+1}.npz")
            np.savez(data_filename, wavelength=result['wavelengths'], intensity=result['intensity'])
            print(f"Data saved to {data_filename}")
            time.sleep(self.isi)
        
    def on_spec_scan(self):
        """Handle spectral scan button"""
        try:
            # Get integration time from your GUI input
            self.int_t = self.spinBox_int_oneScan.value()
            self.isi = self.spinBox_isi_oneScan.value()
            
            # Perform scan
            result = self.spec_controller.scan(self.int_t)
            ints = result["intensity"]
            nms = result['wavelengths']
            max_nm = nms[np.argmax(ints)]
            print(f'max nm:{max_nm}')
            
            if result['success']:
                print('Loading plot...')
                self.load_plot()
            else:
                print(f"Scan failed: {result['error']}")
            return result
        except Exception as e:
            print(f"Scan error: {str(e)}")
        
        
    def on_move_scan(self):
        """Handle move to position and then scans"""
        try:
            # First move to position
            pan = self.spinBox_pan_oneScan.value()
            tilt = self.spinBox_tilt_oneScan.value()
            print(f"Moving to - Pan: {pan}, Tilt: {tilt}")
            
            # Use the motor controller
            self.stepper_controller.move_to(pan, tilt)
            
            # Wait a bit for movement to complete
            time.sleep(0.2)
            
            # Then perform the scan
            self.on_spec_scan()
            
        except Exception as e:
            print(f"Move+Scan error: {str(e)}")
    def on_reset_pos(self):
        """Reset pan and tilt's jsn to zero position"""
        try:
            
            # Use the motor controller
            self.stepper_controller.reset_pos()
            
            # Wait a bit for movement to complete
            time.sleep(0.5)
            
            # Then read from the ESP32's recorded position
            self.stepper_controller.read_pos()
            
        except Exception as e:
            print(f" {str(e)}")
    
    def closeEvent(self, event):
        """Clean up when window is closed"""
        # self.motor_controller.close_connection()
        self. stepper_controller.close_connection()
        event.accept()
        
    # Camera functions
    def load_recent_image(self, camera_id=0):
        """loads most recent image for camera_id"""
        # search_dir = CALI_PATH if camera_id == 0 else CAM_ROI_PATH
        search_dir = GUI_CAM0 if camera_id == 0 else GUI_CAM1
        pattern = f"*cam{camera_id}*.jpg"
        
        try:
            files = glob.glob(os.path.join(search_dir, pattern))
            if files:
                latest = max(files, key=os.path.getmtime)
                # Use your existing labels - the image will replace the text
                widget = self.label_green_camera if camera_id == 0 else self.label_uv_camera
                
                pixmap = QPixmap(latest).scaled(400, 300, Qt.KeepAspectRatio)
                widget.setPixmap(pixmap)
                print(f"Loaded image: {latest} into {widget.objectName()}")
                return latest
            else:
                # Keep the original text if no images found
                print(f"No images found for camera {camera_id}")
                return None
        except Exception as e:
            print(f"Error loading image for camera {camera_id}: {e}")
            return None

    def on_green_shoot(self,output_path=GUI_CAM0,img_idx=0):
        print('pressed green shoot')
        print(output_path)
        """Handle green camera shoot"""
        shutter0 = str(self.spinBox_green_shutter.value()*1000) or "33000"
        gain0 = str(self.doubleSpinBox_green_gain.value()) or "1.12"
        print(f"Green camera shoot clicked - Shutter: {shutter0}ms, Gain: {gain0}")
        print(f"target path{output_path}, no.{img_idx} img")
        QApplication.processEvents()  # Update UI
        
        output_path = output_path or GUI_CAM0
        print(output_path)
        print(["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '0', shutter0, gain0,output_path,str(img_idx)])
        try:
            # Use timeout to prevent hanging
            print('before subprocess call')
            result = subprocess.run(
                ["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '0', shutter0, gain0,output_path,str(img_idx)],
                check=True,
                timeout=30,  # 30 second timeout
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired:
            #self.status_label.setText("Photo capture timed out")
            print(f"Photo capture timed out")
        except subprocess.CalledProcessError as e:
            #self.status_label.setText("Photo capture failed")
            print(f"Error: {e.stderr}")
        except Exception as e:
            #self.status_label.setText("Unexpected error")
            print(f"Unexpected error: {e}")
            
    def on_uv_shoot(self,output_path=GUI_CAM1,img_idx=0):
        """Handle green camera shoot"""
        shutter1 = str(self.spinBox_uv_shutter.value()*1000) or "800000"
        gain1 = str(self.doubleSpinBox_uv_gain.value()) or "1.12"
        print(f"UV camera shoot clicked - Shutter: {shutter1}ms, Gain: {gain1}")
        
        QApplication.processEvents()  # Update UI
        output_path = output_path or GUI_CAM1
        # print(["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '0', shutter0])
        print(type(shutter1))
        try:
            # Use timeout to prevent hanging
            print('before subprocess call')
            result = subprocess.run(
                ["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '1', shutter1, gain1,output_path,str(img_idx)],
                check=True,
                timeout=30,  # 30 second timeout
                capture_output=True,
                text=True
            )
        except subprocess.TimeoutExpired:
            #self.status_label.setText("Photo capture timed out")
            print(f"Photo capture timed out")
        except subprocess.CalledProcessError as e:
            #self.status_label.setText("Photo capture failed")
            print(f"Error: {e.stderr}")
        except Exception as e:
            #self.status_label.setText("Unexpected error")
            print(f"Unexpected error: {e}")
        
    def on_both_shoot(self):
        """Handle both cameras shoot"""
        self.on_green_shoot()
        self.on_uv_shoot()
    def on_update_parameters(self):
        self.pan_min = self.spinBox_pan_min.value()
        self.pan_max = self.spinBox_pan_max.value()
        self.pan_step = self.spinBox_pan_stepsize.value()
        self.num_pan = int((self.pan_max - self.pan_min)/self.pan_step) + 1
        self.label_pan_toUpdatenumStep.setText(str(self.num_pan)) 
        
        self.tilt_min = self.spinBox_tilt_min.value()
        self.tilt_max = self.spinBox_tilt_max.value()
        self.tilt_step = self.spinBox_tilt_stepsize.value()
        self.num_tilt = int((self.tilt_max - self.tilt_min)/self.tilt_step) + 1
        self.label_tilt_toUpdatenumStep.setText(str(self.num_tilt))
        print(f"Updated parameters - Pan steps: {self.num_pan}, Tilt steps: {self.num_tilt}")
        print(f"will take total {self.num_pan*self.num_tilt} photos")  
        
        self.calculate_pano_positions()
    
    def calculate_pano_positions(self):
        if not hasattr(self,"pan_min") or not hasattr(self,'pan_step'):
            self.on_update_parameters()
        pan_positions = np.arange(self.pan_min, self.pan_max + self.pan_step, self.pan_step)
        tilt_positions = np.arange(self.tilt_min, self.tilt_max + self.tilt_step, self.tilt_step)
        print(f"num Pan positions: {len(pan_positions)}, num Tilt positions: {len(tilt_positions)}")
        print(f"total positions: {len(pan_positions)*len(tilt_positions)}")
        cam_path = [(pp,tt) for tt in tilt_positions for pp in pan_positions]
        return cam_path
    
    def on_green_pano(self):
        if not hasattr(self,"num_pan") or not hasattr(self,'num_tilt'):
            self.on_update_parameters()
        if not hasattr(self, 'int_t') or not hasattr(self, 'isi'):
            self.on_spec_scan()
        start_time = time.strftime("%Y%m%d_%H%M%S")
        cam0_data_path = os.path.join(CHESS_PATH, f"{start_time}_cam0")
        os.makedirs(cam0_data_path, exist_ok=True)
        
        print(f"Starting PANO...")
        cam_path = self.calculate_pano_positions()
        print(f"Total positions to take CAM photos: {len(cam_path)}")
        for idx, (pan, tilt) in enumerate(cam_path):
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(cam_path)})")
            self.stepper_controller.move_to(pan, tilt)
            time.sleep(1)  # wait for movement
            
            print(f"Taking pano (GREEN) photo no.{idx+1}/{len(cam_path)} at Pan: {pan}, Tilt: {tilt}")
            self.on_green_shoot(cam0_data_path,img_idx=idx)
            print(f"Waiting for ISI: {self.isi}s before next position...")
            
    def on_start_scam(self):
        start_time = time.strftime("%Y%m%d_%H%M%S")
        scam_data_path = os.path.join(DATA_PATH, f"SCAM_{start_time}")
        os.makedirs(scam_data_path, exist_ok=True)
        
        cam0_data_path = os.path.join(scam_data_path, "cam0")
        cam1_data_path = os.path.join(scam_data_path, "cam1")
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        
        scan_data_path = os.path.join(scam_data_path, "scan_data")
        os.makedirs(scan_data_path, exist_ok=True)
        
        print(f"Data will be saved to: {scam_data_path}")
        
        if not hasattr(self, 'int_t') or not hasattr(self, 'isi'):
            self.on_spec_scan()
        
        if not hasattr(self, 'num_pan') or not hasattr(self, 'num_tilt'):
            self.on_update_parameters()
        print(f"Starting SCAM with Integration Time: {self.int_t}ms, ISI: {self.isi}s")
        
        cam_path = self.calculate_pano_positions()
        print(f"Total positions to take CAM photos: {len(cam_path)}")
        
        # Iterate over all pan and tilt positions
        for idx, (pan, tilt) in enumerate(cam_path):
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(cam_path)})")
            self.stepper_controller.move_to(pan, tilt)
            time.sleep(1)  # wait for movement
            
            print(f"Taking photo scan no.{idx+1}/{len(cam_path)} at Pan: {pan}, Tilt: {tilt}")
            self.on_green_shoot(output_path=cam0_data_path,img_idx=idx)
            self.on_uv_shoot(output_path=cam1_data_path,img_idx=idx)
            
            if not hasattr(self, 'int_t') or not hasattr(self, 'isi'):
                self.on_spec_scan()
            
            print("Performing spectral scan...")
            for tilt_scan in SPEC_TILT_POS:
                self.stepper_controller.move_to(pan,tilt_scan)
                # atm don't change the pan
                time.sleep(2)
                result = self.on_spec_scan()
                
                ints = result["intensity"]
                nms = result['wavelengths']
                max_nm = nms[np.argmax(ints)]
                print(f'max nm:{max_nm}')
                if result:
                    print("Scan successful, saving data...")
                    # Save data logic here
                    data_filename = os.path.join(scan_data_path, f"photo{idx}_scan_pan{pan}_tilt{tilt_scan}.npz")
                    np.savez(data_filename, wavelength=result['wavelengths'], intensity=result['intensity'])
                    print(f"Data saved to {data_filename}")
                else:
                    print(f"Scan failed at Pan: {pan}, Tilt: {tilt} - {result['error']}")
            
                print(f"Waiting for ISI: {self.isi}s before next position...")
                time.sleep(self.isi)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())