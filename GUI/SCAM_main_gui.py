import numpy as np
import glob
import matplotlib.pyplot as plt
import io
import cv2
import time
import sys
import os
import json
import tifffile as tiff

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

# load SCAN-related functions
from spec_scan.spectrometer_controller import SpectrometerController
# from rs_motor.rcmotor_controller import MotorController
from stepper.OS_end.steppers import StepperController
from raw.raw_prepro import cut_raw_black_lines, extract_B_raw,extract_G_raw, adjust_shutter_gain, save_as_jpg, extract_masked_mean
from capture_service import CaptureService
from exposure_controller import ExposureController
from scan_workflows import ScanWorkflows

# define paths/home/ydeng/Github/SCAM/matlab_roi_extraction
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CHESS_PATH = os.path.join(SCAM_PATH, "spherical")
ROI_PATH = os.path.join(SCAM_PATH, "roi")
POINT_SCAN_DATA_PATH = os.path.join(SCAM_PATH, "point_scan_data")
PANO_DATA_PATH = os.path.join(SCAM_PATH, "pano_data")
FULL_SCAM_PATH = os.path.join(SCAM_PATH, "full_scam")
DATA_PATH = os.path.join(SCAM_PATH, "data")
ONE_SCAM_DATA_PATH = os.path.join(SCAM_PATH, "one_scam_data")
SCAN_DATA_PATH = os.path.join(SCAM_PATH, "scan") # point scan
FULL_SCAN_PATH = os.path.join(SCAM_PATH, "full_scan")
EXP_SEARCH_PATH = os.path.join(SCAM_PATH, "exp_search")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
CALI_PATH = os.path.join(SCAM_PATH,"cali")
SCAN_CALI_PATH = os.path.join(SCAM_PATH, "scan_cali")
SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
GUI_PATH = os.path.join(SCAM_PATH, "GUI")
GUI_CAM0 = os.path.join(GUI_PATH,'cam0')
GUI_CAM1 = os.path.join(GUI_PATH,'cam1')
STP_PATH =os.path.join(SCAM_PATH,'stepper')
CAM0_ROI_NPY = os.path.join(SCAM_PATH, "matlab_roi_extraction","cam0_mask.npy")
CAM1_ROI_NPY = os.path.join(SCAM_PATH, "matlab_roi_extraction","cam1_mask.npy")
# SPEC_ROI_CAM_POS=[(0,1),(10,1),(2,1),(10,4),(4,1),(10,0),(1,-4),(10,4)]
#SPEC_ROI_CAM_POS=[(0,0),(0,-10),(0,-20)]
# SPEC_TILT_POS=[18,13,8,3,-2,-7,-12,-18]
#SPEC_TILT_POS=[18,13,3,-7,-18] # when table is against the balcony bar (sunny)
#SPEC_TILT_POS=[13,8,3,-2,-7] # when table is back against the wall(raining)
SPEC_TILT_POS=[]
MIN_SHUTTER,MAX_SHUTTER,STEP_SHUTTER= int(999), int(1033e3), int(1e4)
MIN_GAIN,MAX_GAIN,STEP_GAIN = 1.12, 8.0, 0.2
SHUTTER_SEARCH_RANGE=list(range(MIN_SHUTTER, MAX_SHUTTER, STEP_SHUTTER))
GAIN_SEARCH_RANGE = np.arange(MIN_GAIN, MAX_GAIN, STEP_GAIN).round(1).tolist()

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
        self.capture_service = CaptureService(os.path.join(CALI_PATH, 'libcamera_raw_wrapper.sh'))
        self.scan_workflows = ScanWorkflows(
            point_scan_data_path=POINT_SCAN_DATA_PATH,
            pano_data_path=PANO_DATA_PATH,
            full_scam_path=FULL_SCAM_PATH,
            one_scam_data_path=ONE_SCAM_DATA_PATH,
            full_scan_path=FULL_SCAN_PATH,
            spec_tilt_pos=SPEC_TILT_POS,
        )
        
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
        
        ## initialize parameters
        self.cam0_shutter00 = None
        self.cam0_gain00 = None
        self.shutter1 = None
        self.gain1 = None
        self.cam1_mean1 =None
        self.cam0_roi_mask = np.load(CAM0_ROI_NPY) == 1
        self.cam1_roi_mask = np.load(CAM1_ROI_NPY) == 1
        
        self.connect_signals()
    def save_config(self, config_path):
        """Save current configuration to a JSON file"""
        config = {
            "pan_min": self.spinBox_pan_min.value(),
            "pan_max": self.spinBox_pan_max.value(),
            "pan_step": self.spinBox_pan_stepsize.value(),
            "tilt_min": self.spinBox_tilt_min.value(),
            "tilt_max": self.spinBox_tilt_max.value(),
            "tilt_step": self.spinBox_tilt_stepsize.value(),
            "int_t": self.spinBox_int_oneScan.value(),
            "isi": self.spinBox_isi_oneScan.value(),
            "green_shutter": self.spinBox_green_shutter.value(),
            "green_gain": self.doubleSpinBox_green_gain.value(),
            "uv_shutter": self.spinBox_uv_shutter.value(),
            "uv_gain": self.doubleSpinBox_uv_gain.value()
        }
        if hasattr(self,"cam_path") and self.cam_path is not None:
            config["cam_path"] = np.asarray(self.cam_path).tolist()
        ## debug info
        # for key in config.keys():
        #     print(f'{key}: type: {type(config[key])}')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {config_path}")
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
        self.btn_start_point_scan.clicked.connect(self.on_start_point_scan)# point scan
        self.btn_start_full_scan.clicked.connect(self.on_start_full_scan) 
        self.btn_start_pano.clicked.connect(self.on_start_pano) # only camera-based pano scan
        self.btn_start_point_scam.clicked.connect(self.on_start_point_scam)
        self.btn_start_full_scam.clicked.connect(self.on_start_full_scam)
    
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
                #print('Loading plot...')
                self.load_plot()
            else:
                print(f"Scan failed: {result['error']}")
            return result
        except Exception as e:
            print(f"Scan error: {str(e)}")
        
    def on_move_scan(self):
        """Handle move to position and then scans"""
        try:
            # read the currenet position
            self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
            
            # extract from GUI for the target position
            self.next_pan = self.spinBox_pan_oneScan.value()
            self.next_tilt = self.spinBox_tilt_oneScan.value()
            print(f"Moving to - Pan: {self.next_pan}, Tilt: {self.next_tilt}")
            self.stepper_controller.move_to(self.next_pan, self.next_tilt)
            
            # calculate the wait
            self.motor_wait()
            
            # reassign the current position
            self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
            # Then perform the scan
            self.on_spec_scan()
            
        except Exception as e:
            print(f"Move+Scan error: {str(e)}")
    def on_reset_pos(self):
        """Reset pan and tilt's jsn to zero position"""
        try:
            
            # Use the motor controller
            self.stepper_controller.reset_pos()
            # self.stepper_controller.read_pos()
            
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
        
    def call_libcamera_raw(self,camera_id,shutter,gain,output_dir,img_idx):
        return self.capture_service.call_libcamera_raw(camera_id, shutter, gain, output_dir, img_idx)
    def _remove_capture_pair(self, raw_file):
        self.capture_service.remove_capture_pair(raw_file)

    def _save_jpg_from_raw(self, raw_file, camera_id):
        self.capture_service.save_jpg_from_raw(raw_file, camera_id)

    def _promote_capture_pair(self, raw_file, final_dir):
        return self.capture_service.promote_capture_pair(raw_file, final_dir)

    def call_libcamera_raw_pair(self, green_shutter, green_gain, green_output_dir,
                                uv_shutter, uv_gain, uv_output_dir, img_idx):
        return self.capture_service.call_libcamera_raw_pair(
            green_shutter, green_gain, green_output_dir, uv_shutter, uv_gain, uv_output_dir, img_idx
        )
    def on_green_shoot(self,output_path=None,img_idx=0,save_jpg=True,process_events=False):
        if output_path is None or output_path is False:
            output_path = GUI_CAM0
        ## if this is the first green shoot
        if self.cam0_shutter00 is None and self.cam0_gain00 is None:
            shutter0 = str(self.spinBox_green_shutter.value()) or "33"
            gain0 = str(self.doubleSpinBox_green_gain.value()) or "1.12"
        else:
            shutter0 = self.cam0_shutter00
            gain0 = self.cam0_gain00
        if process_events:
            QApplication.processEvents()
        
        final_shutter0 = str(shutter0)
        final_gain0 = str(gain0)
        output_fname = None
        raw_2d_G = None
        MAX_GREEN_RETRY = 3
        GREEN_TOL = 0.05

        # Single bounded loop: adjust green exposure to match UV ROI mean.
        for _ in range(MAX_GREEN_RETRY):
            output_fname = self.call_libcamera_raw(0, final_shutter0, final_gain0, output_path, img_idx)
            while os.path.exists(output_fname) is False:
                print(f"Waiting for Green image file to be created: {output_fname}")

            raw_2d = cut_raw_black_lines(output_fname)
            raw_2d_G = extract_G_raw(raw_2d)
            self.cam0_mean1 = extract_masked_mean(raw_2d_G, 'cam0')

            if ExposureController.green_in_tolerance(self.cam1_mean1, self.cam0_mean1, tol=GREEN_TOL):
                break

            change_factor = ExposureController.green_change_factor(
                self.cam1_mean1, self.cam0_mean1, min_factor=0.7, max_factor=1.4
            )
            next_shutter, next_gain = adjust_shutter_gain(float(final_shutter0), float(final_gain0), change_factor)
            if str(next_shutter) == str(final_shutter0) and str(next_gain) == str(final_gain0):
                break

            # Intermediate frame is not final; remove before next retry.
            self._remove_capture_pair(output_fname)
            final_shutter0, final_gain0 = str(next_shutter), str(next_gain)
        ## store the first green img's shutter and gain for the later use in the ground mode
        self.cam0_shutter00 = str(final_shutter0); self.cam0_gain00 = str(final_gain0)
        if save_jpg:
            save_as_jpg(raw_2d_G,output_fname.replace('.raw','_G.jpg'))
        return output_fname
                
    def on_uv_shoot(self,output_path=None,img_idx=0,save_jpg=True,process_events=False):
        if output_path is None or output_path is False:
            output_path = GUI_CAM1
        """Handle green camera shoot"""
        if self.shutter1 is None or self.gain1 is None:
            shutter1 = str(self.spinBox_uv_shutter.value()) or "33"
            gain1 = str(self.doubleSpinBox_uv_gain.value()) or "1.12"
        else:
            shutter1 = self.shutter1
            gain1 = self.gain1
        if process_events:
            QApplication.processEvents()
        output_fname = self.call_libcamera_raw(1,shutter1,gain1,output_path,img_idx)
        while os.path.exists(output_fname) is False:
            print(f"Waiting for UV image file to be created: {output_fname}")
            time.sleep(1)
    
        raw_2d = cut_raw_black_lines(output_fname)
        raw_2d_B = extract_B_raw(raw_2d)
        self.cam1_mean1, p99, sat_frac = ExposureController.uv_metrics(raw_2d_B, self.cam1_roi_mask)

        print(f'initial cam1_mean1: {self.cam1_mean1}')
        MAX_EXPO_RETRY = 3
        TARGET_LOW = 4096 * 1.05
        TARGET_HIGH = 42000
        P99_MAX = 64500
        SAT_FRAC_MAX = 0.4  # 1.0%

        for _ in range(MAX_EXPO_RETRY):
            accepted, clip_ok = ExposureController.uv_accept(
                self.cam1_mean1, p99, sat_frac, TARGET_LOW, TARGET_HIGH, P99_MAX, SAT_FRAC_MAX
            )
            if accepted:
                break
            if self.cam1_mean1 is None or self.cam1_mean1 <= 0:
                raise RuntimeError(f"Invalid cam1_mean1: {self.cam1_mean1}")

            if os.path.exists(output_fname):
                os.remove(output_fname)
                os.remove(output_fname.replace('.raw','.json'))

            change_factor = ExposureController.uv_change_factor(
                self.cam1_mean1, p99, sat_frac, clip_ok,
                TARGET_LOW, TARGET_HIGH, P99_MAX, SAT_FRAC_MAX, clip_safety=0.97
            )

            shutter1, gain1 = adjust_shutter_gain(float(shutter1), float(gain1), change_factor)
            output_fname = self.call_libcamera_raw(1, shutter1, gain1, output_path, img_idx)

            # wait max.30 seconds for the new image to be created, otherwise raise timeout error
            for _ in range(3): 
                if os.path.exists(output_fname):
                    break
                time.sleep(1)
            else:
                raise TimeoutError(f"UV image not created in time: {output_fname}")
            raw_2d = cut_raw_black_lines(output_fname)
            raw_2d_B = extract_B_raw(raw_2d)
            self.cam1_mean1, p99, sat_frac = ExposureController.uv_metrics(raw_2d_B, self.cam1_roi_mask)
            print(f'uv exposure check: mean={self.cam1_mean1:.1f}, p99={p99:.1f}, sat_frac={sat_frac:.5f}')
        else:
            print(f"Exposure not converged after {MAX_EXPO_RETRY} retries, use last values.")
            
        self.shutter1 = shutter1;self.gain1 = gain1
        if save_jpg:
            save_as_jpg(raw_2d_B,output_fname.replace('.raw','_B.jpg'))
        return output_fname
            
    def on_both_shoot(self, green_output_path=None, uv_output_path=None, img_idx=0,
                     replace_with_simultaneous=True):
        """Handle both cameras shoot"""
        # Qt clicked(bool) can pass False into the first positional arg.
        if isinstance(green_output_path, bool):
            green_output_path = None
        if isinstance(uv_output_path, bool):
            uv_output_path = None

        if green_output_path is None:
            green_output_path = GUI_CAM0
        if uv_output_path is None:
            uv_output_path = GUI_CAM1
        seq_green_path = os.path.join(green_output_path, "_staging_seq")
        seq_uv_path = os.path.join(uv_output_path, "_staging_seq")
        os.makedirs(seq_green_path, exist_ok=True)
        os.makedirs(seq_uv_path, exist_ok=True)

        # First pass: sequential captures to derive balanced exposure settings.
        uv_raw = self.on_uv_shoot(output_path=seq_uv_path, img_idx=img_idx, save_jpg=False)
        green_raw = self.on_green_shoot(output_path=seq_green_path, img_idx=img_idx, save_jpg=False)

        if not replace_with_simultaneous:
            return green_raw, uv_raw

        green_shutter = getattr(self, "cam0_shutter00", str(self.spinBox_green_shutter.value()))
        green_gain = getattr(self, "cam0_gain00", str(self.doubleSpinBox_green_gain.value()))
        uv_shutter = getattr(self, "shutter1", str(self.spinBox_uv_shutter.value()))
        uv_gain = getattr(self, "gain1", str(self.doubleSpinBox_uv_gain.value()))

        sim_green_raw, sim_uv_raw = self.call_libcamera_raw_pair(
            green_shutter=green_shutter,
            green_gain=green_gain,
            green_output_dir=green_output_path,
            uv_shutter=uv_shutter,
            uv_gain=uv_gain,
            uv_output_dir=uv_output_path,
            img_idx=img_idx
        )
        if sim_green_raw and sim_uv_raw and os.path.exists(sim_green_raw) and os.path.exists(sim_uv_raw):
            self._remove_capture_pair(green_raw)
            self._remove_capture_pair(uv_raw)
            self._save_jpg_from_raw(sim_green_raw, camera_id=0)
            self._save_jpg_from_raw(sim_uv_raw, camera_id=1)
            print("Sequential pair replaced by simultaneous pair.")
            return sim_green_raw, sim_uv_raw

        # Simultaneous call failed: keep sequential final pair and export jpg only for those final files.
        green_raw = self._promote_capture_pair(green_raw, green_output_path)
        uv_raw = self._promote_capture_pair(uv_raw, uv_output_path)
        self._save_jpg_from_raw(green_raw, camera_id=0)
        self._save_jpg_from_raw(uv_raw, camera_id=1)
        print("Simultaneous replacement failed; keeping sequential captures.")
        return green_raw, uv_raw
        
    def on_update_parameters(self):
        """"Update parameters from UI"""
        self.pan_min = self.spinBox_pan_min.value()
        self.pan_max = self.spinBox_pan_max.value()
        self.pan_step = self.spinBox_pan_stepsize.value()
        self.num_pan = int((self.pan_max - self.pan_min)/self.pan_step) + 1
        
        self.tilt_min = self.spinBox_tilt_min.value()
        self.tilt_max = self.spinBox_tilt_max.value()
        self.tilt_step = self.spinBox_tilt_stepsize.value()
        self.num_tilt = int((self.tilt_max - self.tilt_min)/self.tilt_step) + 1
        self.label_tilt_toUpdatenumStep.setText(str(self.num_tilt))
        print(f"Updated parameters - Pan steps: {self.num_pan}, Tilt steps: {self.num_tilt}")
        print(f"will take total {self.num_pan*self.num_tilt} photos")
        
        self.pan_oneScan = self.spinBox_pan_oneScan.value()
        self.tilt_oneScan = self.spinBox_tilt_oneScan.value()
        self.int_oneScan = self.spinBox_int_oneScan.value()
        
        ## horrible duplicates, a make-do solution rn but need fix
        self.isi_oneScan = self.spinBox_isi_oneScan.value()
        self.isi = self.spinBox_isi_oneScan.value()
    def motor_wait(self):
        delta_t = 0.3*(abs(self.next_tilt-self.current_tilt))+0.1*abs(self.next_pan-self.current_pan)
        time.sleep(int(delta_t)+1)
    def calculate_pano_positions(self):
        if not hasattr(self,"pan_min") or not hasattr(self,'pan_step'):
            self.on_update_parameters()
        self.pan_positions = np.arange(self.pan_min, self.pan_max + self.pan_step, self.pan_step)
        self.tilt_positions = np.arange(self.tilt_min, self.tilt_max + self.tilt_step, self.tilt_step)
        print(f"num Pan positions: {len(self.pan_positions)}, num Tilt positions: {len(self.tilt_positions)}")
        print(f"total positions: {len(self.pan_positions)*len(self.tilt_positions)}")
        cam_path = [(pp,tt) for tt in self.tilt_positions for pp in self.pan_positions]
        return cam_path
    def on_start_full_scan(self):
        self.scan_workflows.start_full_scan(self)
    
    def adjust_int_t(self,int_t,num_max_adjust=3,min_ADC=0.25*16383,max_ADC=0.75*16383,target_ADC=0.5*16383):
        for _ in range(num_max_adjust):
            measurement = self.spec_controller.scan(int_t)
            peak = measurement["intensity"].max()
            if min_ADC <= peak <= max_ADC: # linearity range for the STUV-100
                break
            factor = target_ADC / peak
            
            # stability clamp
            factor = max(0.5, min(20.0, factor))
            new_int = int(int_t * factor)
            
            new_int = max(1, min(5999, new_int)) # make sure new_int is between 0.156microsec and 600ms
            print(" int_t after adjustment:", new_int)
            if new_int == int_t:
                break
            int_t = new_int
        
        return int_t
        
    def on_start_point_scan(self):
        self.scan_workflows.start_point_scan(self)
        
    def on_start_pano(self):
        self.scan_workflows.start_pano(self)
        
    def on_start_point_scam(self):
        self.scan_workflows.start_point_scam(self)
            
    
    def on_start_full_scam(self):
        self.scan_workflows.start_full_scam(self)
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
