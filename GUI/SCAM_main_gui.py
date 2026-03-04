import numpy as np
import glob
import matplotlib.pyplot as plt
import io
import cv2
import time
import subprocess
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
SPEC_TILT_POS=[18,13,3,-7,-18] # when table is against the balcony bar (sunny)
#SPEC_TILT_POS=[13,8,3,-2,-7] # when table is back against the wall(raining)
# SPEC_TILT_POS=[]
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
        cmd = ["/bin/bash", os.path.join(CALI_PATH, 'libcamera_raw_wrapper.sh'), 'capture_raw',
               str(camera_id), str(gain), str(shutter), output_dir, str(img_idx)]
        fname = f"{output_dir}/cam{camera_id}_gain{gain}_{shutter}ms_{img_idx}.raw"
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    backoff = 0.4 * attempt
                    print(f"Retrying capture attempt {attempt}/{max_attempts} after {backoff:.1f}s backoff")
                    time.sleep(backoff)
                else:
                    # small pacing delay reduces camera pipeline thrash between rapid calls
                    time.sleep(0.25)
                result = subprocess.run(
                    cmd,
                    check=True,
                    timeout=35,
                    capture_output=True,
                    text=True
                )
                for _ in range(10):
                    if os.path.exists(fname):
                        break
                    time.sleep(0.3)
                if os.path.exists(fname):
                    return fname
                print(f"Capture succeeded but output file not found yet: {fname}")
            except subprocess.TimeoutExpired:
                print("Photo capture timed out")
            except subprocess.CalledProcessError as e:
                print(f"Error: {e.stderr}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        return fname
    def _remove_capture_pair(self, raw_file):
        if raw_file and os.path.exists(raw_file):
            os.remove(raw_file)
        meta_file = raw_file.replace('.raw', '.json') if raw_file else None
        if meta_file and os.path.exists(meta_file):
            os.remove(meta_file)
        if raw_file:
            base = raw_file.replace('.raw', '')
            for jpg_file in (f"{base}_G.jpg", f"{base}_B.jpg", f"{base}.jpg"):
                if os.path.exists(jpg_file):
                    os.remove(jpg_file)

    def _save_jpg_from_raw(self, raw_file, camera_id):
        if not raw_file or not os.path.exists(raw_file):
            return
        raw_2d = cut_raw_black_lines(raw_file)
        if int(camera_id) == 0:
            chan = extract_G_raw(raw_2d)
            save_as_jpg(chan, raw_file.replace('.raw', '_G.jpg'))
        else:
            chan = extract_B_raw(raw_2d)
            save_as_jpg(chan, raw_file.replace('.raw', '_B.jpg'))

    def _promote_capture_pair(self, raw_file, final_dir):
        if not raw_file:
            return None
        final_raw = os.path.join(final_dir, os.path.basename(raw_file))
        meta_src = raw_file.replace('.raw', '.json')
        meta_dst = final_raw.replace('.raw', '.json')
        if os.path.exists(raw_file):
            os.replace(raw_file, final_raw)
        if os.path.exists(meta_src):
            os.replace(meta_src, meta_dst)
        return final_raw

    def call_libcamera_raw_pair(self, green_shutter, green_gain, green_output_dir,
                                uv_shutter, uv_gain, uv_output_dir, img_idx):
        try:
            cmd = [
                "/bin/bash",
                os.path.join(CALI_PATH, 'libcamera_raw_wrapper.sh'),
                'capture_raw_pair',
                str(green_gain), str(green_shutter), green_output_dir,
                str(uv_gain), str(uv_shutter), uv_output_dir,
                str(img_idx)
            ]
            result = subprocess.run(
                cmd,
                check=True,
                timeout=45,
                capture_output=True,
                text=True
            )
            green_raw = f"{green_output_dir}/cam0_gain{green_gain}_{green_shutter}ms_{img_idx}.raw"
            uv_raw = f"{uv_output_dir}/cam1_gain{uv_gain}_{uv_shutter}ms_{img_idx}.raw"
            return green_raw, uv_raw
        except subprocess.TimeoutExpired:
            print("Simultaneous photo capture timed out")
        except subprocess.CalledProcessError as e:
            print(f"Simultaneous capture failed: {e.stderr}")
        except Exception as e:
            print(f"Unexpected simultaneous capture error: {e}")
        return None, None
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

            if self.cam1_mean1 is None or self.cam0_mean1 is None or self.cam0_mean1 <= 0:
                break
            ratio = self.cam1_mean1 / self.cam0_mean1
            if (1.0 - GREEN_TOL) <= ratio <= (1.0 + GREEN_TOL):
                break

            change_factor = max(0.7, min(1.4, float(ratio)))
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
        self.cam1_mean1=extract_masked_mean(raw_2d_B,'cam1')
        roi_vals = raw_2d_B[self.cam1_roi_mask].astype(np.float64)
        p99 = np.percentile(roi_vals, 99.0)
        sat_frac = (roi_vals >= 65500).mean()

        print(f'initial cam1_mean1: {self.cam1_mean1}')
        MAX_EXPO_RETRY = 3
        TARGET_LOW = 4096 * 1.05
        TARGET_HIGH = 42000
        P99_MAX = 64500
        SAT_FRAC_MAX = 0.4  # 1.0%

        for _ in range(MAX_EXPO_RETRY):
            mean_ok = TARGET_LOW <= self.cam1_mean1 <= TARGET_HIGH
            clip_ok = (p99 <= P99_MAX) and (sat_frac <= SAT_FRAC_MAX)
            if mean_ok and clip_ok:
                break
            if self.cam1_mean1 is None or self.cam1_mean1 <= 0:
                raise RuntimeError(f"Invalid cam1_mean1: {self.cam1_mean1}")

            if os.path.exists(output_fname):
                os.remove(output_fname)
                os.remove(output_fname.replace('.raw','.json'))

            if not clip_ok:
                p99_factor = P99_MAX / max(p99, 1.0)
                sat_factor = SAT_FRAC_MAX / max(sat_frac, 1e-9)
                # Prioritize clipping avoidance; keep a safety margin.
                change_factor = min(p99_factor, sat_factor, 1.0) * 0.97
            elif self.cam1_mean1 < TARGET_LOW:
                change_factor = TARGET_LOW / self.cam1_mean1
            else:
                change_factor = TARGET_HIGH / self.cam1_mean1

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
            self.cam1_mean1 = extract_masked_mean(raw_2d_B, 'cam1')
            roi_vals = raw_2d_B[self.cam1_roi_mask].astype(np.float64)
            p99 = np.percentile(roi_vals, 99.0)
            sat_frac = (roi_vals >= 65500).mean()
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
        print("I AM HERE!! FULL SCAN!")
        start_time = time.strftime("%Y%m%d_%H%M%S")
        full_scan_save_path = os.path.join(FULL_SCAN_PATH, f"FULL_SCAN_{start_time}")
        os.makedirs(full_scan_save_path, exist_ok=True)
        """Start full spectral scan for scene reconstruction"""
        try:
            self.on_update_parameters()
            # hardcode pan/tilt step to 1 degree
            self.pan_step = 1
            self.tilt_step = 1
            self.cam_path = self.calculate_pano_positions()
            # save the scan positions
            np.savez(os.path.join(full_scan_save_path,'scan_positions.npz'),positions=self.cam_path)
            for idx, (pan, tilt) in enumerate(self.cam_path):
                ## move motors
                # where we are
                self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
                # where we want to go
                self.next_pan = pan
                self.next_tilt = tilt
                # move and wait
                self.stepper_controller.move_to(self.next_pan, self.next_tilt)
                self.motor_wait()
                print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(self.cam_path)})")
                # adjust the integration time based on the previous scan result at the same tilt position
                
                self.int_oneScan = self.adjust_int_t(self.int_oneScan)

                result_ = self.spec_controller.scan(self.int_oneScan)
                result_['motor_pan'] = pan
                result_['motor_tilt'] = tilt
                result_['ts'] = time.strftime("%Y%m%d_%H%M%S")

                np.save(os.path.join(full_scan_save_path, f"full_scan_{idx}_{pan}_{tilt}"), result_)
                time.sleep(self.isi_oneScan)
        except Exception as e:
            print(f"Error during full scan: {str(e)}")
    
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
        """
        Start a point scan by capturing spectral data at specific positions.
        
        This method moves the stepper motors to predefined positions for sky and ground scans,
        captures preview images, and performs spectral scans at each position. The data is saved
        to the appropriate directories for further analysis.
        """
        start_time = time.strftime("%Y%m%d_%H%M%S")
        point_scan_save_path = os.path.join(POINT_SCAN_DATA_PATH, f"POINT_SCAN_{start_time}")
        sky_save_path = os.path.join(point_scan_save_path, f"sky_scan")
        ground_save_path = os.path.join(point_scan_save_path, f"ground_scan")
        preview_cam0_path = os.path.join(point_scan_save_path, "preview_cam0")
        preview_cam1_path = os.path.join(point_scan_save_path, "preview_cam1")
        loc_save_dict = {'sky':sky_save_path,'ground':ground_save_path}
        
        os.makedirs(point_scan_save_path, exist_ok=True)
        os.makedirs(sky_save_path, exist_ok=True)
        os.makedirs(ground_save_path, exist_ok=True)
        os.makedirs(preview_cam0_path, exist_ok=True)
        os.makedirs(preview_cam1_path, exist_ok=True)
        """Start solely spectral scan"""
        # with two photos preview
        # scan one visual angle in the sky -> one visual angle in the ground
        try:
            self.on_update_parameters()
            sky_tilt=self.tilt_max
            ground_tilt=self.tilt_min
            pan = self.pan_oneScan
            POINT_SCAN_INTERATION = 3
            point_scan_config = {
                "pan": pan,
                "sky_tilt": sky_tilt,
                "ground_tilt": ground_tilt,
                "num_iteration": POINT_SCAN_INTERATION
            }
            # save before start
            with open(os.path.join(point_scan_save_path,'point_scan_config.json'), 'w') as f:
                json.dump(point_scan_config, f, indent=4)
            
            ## take photo preview at the two positions before the scan
            for tt,tilt in enumerate([sky_tilt,ground_tilt]):
                ## move the motors
                self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
                self.next_pan = pan
                self.next_tilt = tilt
                
                self.stepper_controller.move_to(self.next_pan, self.next_tilt)
                self.motor_wait()
                ## take a photo preivew
                green_preview_raw, uv_preview_raw = self.on_both_shoot(
                    green_output_path=preview_cam0_path,
                    uv_output_path=preview_cam1_path,
                    img_idx=tt
                )
                # Keep the point-scan preview behavior lightweight: remove temporary preview captures.
                self._remove_capture_pair(green_preview_raw)
                self._remove_capture_pair(uv_preview_raw)
                
            print(f"Starting POINT SCAN:")
            # init integration time for different tilts
            int_t_dict = {
                'sky': self.int_oneScan,
                'ground': self.int_oneScan
            }
            for ii in range(POINT_SCAN_INTERATION): # max 3 iteration testing
                for tt,key in zip([sky_tilt,ground_tilt],['sky','ground']):
                    ## move the motors
                    self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
                    self.next_pan = pan
                    self.next_tilt = tt
                    
                    self.stepper_controller.move_to(self.next_pan, self.next_tilt)
                    self.motor_wait()
                    
                    # adjust integration time based on the previous scan result at the same tilt position
                    int_t_dict[key] = self.adjust_int_t(int_t_dict[key])
                    print('finished adjust_int_t(), now int_t for {} tilt is {}'.format(key,int_t_dict[key]))
                    result_ = self.spec_controller.scan(int_t_dict[key])
                    result_['motor_pan'] = pan
                    result_['motor_tilt'] = tt
                    result_['ts'] = time.strftime("%Y%m%d_%H%M%S")
                    np.save(os.path.join(loc_save_dict[key], f"{key}_scan_{ii}"), result_)
                    time.sleep(self.isi_oneScan)
        except Exception as e:
            print(f"Error during POINT SCAN: {str(e)}")
        
    def on_start_pano(self):
        self.on_update_parameters()
        
        start_time = time.strftime("%Y%m%d_%H%M%S")
        pano_data_path = os.path.join(PANO_DATA_PATH, f"PANO_{start_time}")
        os.makedirs(pano_data_path, exist_ok=True)
        
        cam0_data_path = os.path.join(pano_data_path, "cam0")
        cam1_data_path = os.path.join(pano_data_path, "cam1")
        
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        
        print(f"Starting PANO...")
        self.cam_path = self.calculate_pano_positions()
        self.save_config(os.path.join(pano_data_path, "pano_config.json"))
        print(f"Total positions to take CAM photos: {len(self.cam_path)}")
        RECALIBRATE_EVERY = 4
        for idx, (pan, tilt) in enumerate(self.cam_path):
            ## move the motors
            self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
            self.next_pan = pan
            self.next_tilt = tilt
            
            self.stepper_controller.move_to(self.next_pan, self.next_tilt)
            if self.current_tilt == self.next_tilt:
                # Fast path for same-tilt pano stepping; keep conservative wait for tilt changes.
                pan_delta = abs(self.next_pan - self.current_pan)
                time.sleep(max(0.35, 0.08 * pan_delta + 0.25))
            else:
                self.motor_wait()
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(self.cam_path)})")
        
            ## take photos with both cameras
            # deactivate uv_for inside-test run
            print(f"Taking pano (UV) photo no.{idx+1}/{len(self.cam_path)} at Pan: {pan}, Tilt: {tilt}")
            need_recalibrate = (
                idx == 0 or
                (idx % RECALIBRATE_EVERY == 0) or
                self.cam0_shutter00 is None or self.cam0_gain00 is None or
                self.shutter1 is None or self.gain1 is None
            )
            if need_recalibrate:
                self.on_both_shoot(
                    green_output_path=cam0_data_path,
                    uv_output_path=cam1_data_path,
                    img_idx=idx
                )
            else:
                sim_green_raw, sim_uv_raw = self.call_libcamera_raw_pair(
                    green_shutter=self.cam0_shutter00,
                    green_gain=self.cam0_gain00,
                    green_output_dir=cam0_data_path,
                    uv_shutter=self.shutter1,
                    uv_gain=self.gain1,
                    uv_output_dir=cam1_data_path,
                    img_idx=idx
                )
                if sim_green_raw and sim_uv_raw and os.path.exists(sim_green_raw) and os.path.exists(sim_uv_raw):
                    self._save_jpg_from_raw(sim_green_raw, camera_id=0)
                    self._save_jpg_from_raw(sim_uv_raw, camera_id=1)
                else:
                    # Fallback: recover with full sequential calibration + replacement.
                    self.on_both_shoot(
                        green_output_path=cam0_data_path,
                        uv_output_path=cam1_data_path,
                        img_idx=idx
                    )

            print(f"Waiting for ISI: {self.isi}s before next position...")
        print("the full pano session completed.")
        
    def on_start_point_scam(self):
        # print("I AM HERE!! SCAM ONE POSITION!")
        NUM_CAM = 80
        NUM_SCAN_ITERATION = 3
        RECALIBRATE_EVERY = 4
        start_time = time.strftime("%Y%m%d_%H%M%S")
        scam_data_path = os.path.join(ONE_SCAM_DATA_PATH, f"SCAM_{start_time}")
        os.makedirs(scam_data_path, exist_ok=True)
        
        cam0_data_path = os.path.join(scam_data_path, "cam0")
        cam1_data_path = os.path.join(scam_data_path, "cam1")
        scan_data_path = os.path.join(scam_data_path, "scan_data")
        
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        os.makedirs(scan_data_path, exist_ok=True)
        
        print(f"Data will be saved to: {scam_data_path}")
        self.on_update_parameters()
        self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
        self.next_pan = self.pan_oneScan
        self.next_tilt = self.tilt_oneScan
        
        print(f"Taking CAM at Pan: {self.pan_oneScan}, Tilt: {self.tilt_oneScan}")
        self.stepper_controller.move_to(self.pan_oneScan, self.tilt_oneScan)
        self.motor_wait()
        # init integration time for different tilts
        int_t_dict = {tilt: self.int_oneScan for tilt in SPEC_TILT_POS}
        
        ## start the loop of taking photos and spectra at the same position, to test the stability of the system and the repeatability of the measurement
        for cc in range(NUM_CAM):
            self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
            self.next_pan,self.next_tilt = self.pan_oneScan, self.tilt_oneScan
            
            self.stepper_controller.move_to(self.pan_oneScan, self.tilt_oneScan)
            self.motor_wait()
            
            print(f"Taking pano (UV) photo no.{cc+1}/{NUM_CAM} at Pan: {self.pan_oneScan}, Tilt: {self.pan_oneScan}")
            need_recalibrate = (
                cc == 0 or
                (cc % RECALIBRATE_EVERY == 0) or
                self.cam0_shutter00 is None or self.cam0_gain00 is None or
                self.shutter1 is None or self.gain1 is None
            )
            if need_recalibrate:
                self.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=cc)
            else:
                sim_green_raw, sim_uv_raw = self.call_libcamera_raw_pair(
                    green_shutter=self.cam0_shutter00,
                    green_gain=self.cam0_gain00,
                    green_output_dir=cam0_data_path,
                    uv_shutter=self.shutter1,
                    uv_gain=self.gain1,
                    uv_output_dir=cam1_data_path,
                    img_idx=cc
                )
                if sim_green_raw and sim_uv_raw and os.path.exists(sim_green_raw) and os.path.exists(sim_uv_raw):
                    self._save_jpg_from_raw(sim_green_raw, camera_id=0)
                    self._save_jpg_from_raw(sim_uv_raw, camera_id=1)
                else:
                    self.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=cc)
            for ii in range(NUM_SCAN_ITERATION):
                for ss,tilt in enumerate(SPEC_TILT_POS):
                    self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
                    self.next_pan,self.next_tilt = self.pan_oneScan, tilt
                    
                    # move to position
                    self.stepper_controller.move_to(self.next_pan, self.next_tilt)
                    self.motor_wait()
                    
                    # adjust integration time based on the previous scan result at the same tilt position
                    int_t_dict[tilt] = self.adjust_int_t(int_t_dict[tilt])
                    print('finished adjust_int_t(), now int_t for {} tilt is {}'.format(tilt,int_t_dict[tilt]))
                    
                    # scan and save result
                    result_ = self.spec_controller.scan(int_t_dict[tilt])
                    result_['motor_pan'] = self.pan_oneScan
                    result_['motor_tilt'] = tilt
                    result_['ts'] = time.strftime("%Y%m%d_%H%M%S")
                    np.save(os.path.join(scan_data_path, f"scan_iter{cc}_{ii}_pan{self.pan_oneScan}_tilt{tilt}"), result_)
    def on_start_full_scam(self):
        start_time = time.strftime("%Y%m%d_%H%M%S")
        full_scam_data_path = os.path.join(FULL_SCAM_PATH, f"SCAM_{start_time}")
        os.makedirs(full_scam_data_path, exist_ok=True)
        
        cam0_data_path = os.path.join(full_scam_data_path, "cam0")
        cam1_data_path = os.path.join(full_scam_data_path, "cam1")
        scan_data_path = os.path.join(full_scam_data_path, "scan_data")
        
        os.makedirs(cam0_data_path, exist_ok=True)
        os.makedirs(cam1_data_path, exist_ok=True)
        os.makedirs(scan_data_path, exist_ok=True)
        
        print(f"Data will be saved to: {full_scam_data_path}")
        self.on_update_parameters()
        self.cam_path = self.calculate_pano_positions()
        self.save_config(os.path.join(full_scam_data_path, "scam_config.json"))
        print(f"Total positions to take CAM photos: {len(self.cam_path)}")
        
        # Iterate over all pan and tilt positions
        for idx, (pan, tilt) in enumerate(self.cam_path):
            print(f"Moving to Pan: {pan}, Tilt: {tilt} ({idx+1}/{len(self.cam_path)})")
            self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
            self.next_pan = pan
            self.next_tilt = tilt
            
            self.stepper_controller.move_to(self.next_pan, self.next_tilt)
            self.motor_wait()
            
            print(f"Taking photo scan no.{idx+1}/{len(self.cam_path)} at Pan: {pan}, Tilt: {tilt}")
            self.on_both_shoot(green_output_path=cam0_data_path, uv_output_path=cam1_data_path, img_idx=idx)
            print('finished simultaneous replacement photo pair')
            
            ## if SPEC_TILT_POS is defined, perform spectral scan at different tilt positions for the same pan position
            if len(SPEC_TILT_POS)>0:
                print("Performing spectral scan...")
                for tilt_scan in SPEC_TILT_POS:
                    self.current_pan,self.current_tilt = self.stepper_controller.read_pos()
                    self.next_pan = pan
                    self.next_tilt = tilt_scan
                
                    self.stepper_controller.move_to(self.next_pan, self.next_tilt)
                    self.motor_wait()
                    # adjust the integration time based on the previous scan result at the same tilt position
                    self.int_oneScan = self.adjust_int_t(self.int_oneScan)
                    
                    result = self.spec_controller.scan(self.int_oneScan)
                    # print(f'max nm:{max_nm}')
                    if result:
                        #print("Scan successful, saving data...")
                        # Save data logic here
                        data_filename = os.path.join(scan_data_path, f"photo{idx}_scan_pan{pan}_tilt{tilt_scan}.npz")
                        np.savez(data_filename, wavelength=result['wavelengths'], intensity=result['intensity'])
                        #print(f"Data saved to {data_filename}")
                    else:
                        print(f"Scan failed at Pan: {pan}, Tilt: {tilt} - {result['error']}")
                
                    print(f"Waiting for ISI: {self.isi}s before next position...")
                    time.sleep(self.isi)
        print("the full SCAM session completed.")
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
