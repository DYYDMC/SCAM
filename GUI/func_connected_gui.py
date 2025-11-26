import numpy as np
import glob
import matplotlib.pyplot as plt
import io
import time
import subprocess
import sys
import os
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
from rs_motor.motor_controller import MotorController

# define paths
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
CALI_PATH = os.path.join(SCAM_PATH,"cali")
SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
GUI_PATH = os.path.join(SCAM_PATH, "GUI")
RS_PATH = os.path.join(SCAM_PATH,'rs_motor')
COORDINATE_inds =[0,3,6,2,5,8,4,7,1]
COORDINATES = np.arange(0,45,5)

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
        self.motor_controller = MotorController()
        
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
        
        # Camera section
        self.btn_green_shoot.clicked.connect(self.on_green_shoot)
        self.btn_uv_shoot.clicked.connect(self.on_uv_shoot)
        self.btn_both_shoot.clicked.connect(self.on_both_shoot)
        
        # Calibration section
        self.btn_start_calibration.clicked.connect(self.on_start_calibration)
        self.btn_stop_calibration.clicked.connect(self.on_stop_calibration)
    
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
    def on_spec_scan(self):
        """Handle spectral scan button"""
        try:
            # Get integration time from your GUI input
            int_time = self.spinBox_int_oneScan.value()
            
            # Perform scan
            result = self.spec_controller.scan(int_time)
            ints = result["intensity"]
            nms = result['wavelengths']
            max_nm = nms[np.argmax(ints)]
            print(f'max nm:{max_nm}')
            print('Scan result:', result)
            
            if result['success']:
                print('Loading plot...')
                self.load_plot()
            else:
                print(f"Scan failed: {result['error']}")
                
        except Exception as e:
            print(f"Scan error: {str(e)}")
        
        pan = self.spinBox_pan.value()*-1
        tilt = self.spinBox_tilt.value()
        print(f"Scan clicked - Integration: {int_time}ms, Pan: {pan}, Tilt: {tilt}")
    
        
    def on_move_scan(self):
        """Handle move to position and then scans"""
        try:
            # First move to position
            pan = self.spinBox_pan.value()*-1
            tilt = self.spinBox_tilt.value()
            print(f"Moving to - Pan: {pan}, Tilt: {tilt}")
            
            # Use the motor controller
            self.motor_controller.move_to(pan, tilt)
            
            # Wait a bit for movement to complete
            time.sleep(0.5)
            
            # Then perform the scan
            self.on_spec_scan()
            
        except Exception as e:
            print(f"Move+Scan error: {str(e)}")
    
    def closeEvent(self, event):
        """Clean up when window is closed"""
        self.motor_controller.close_connection()
        event.accept()
        
    # Camera functions
    def load_recent_image(self, camera_id=0):
        """loads most recent image for camera_id"""
        search_dir = CALI_PATH if camera_id == 0 else CAM_ROI_PATH
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

    def on_green_shoot(self):
        """Handle green camera shoot"""
        shutter0 = str(self.spinBox_green_shutter.value()*1000) or "33000"
        print(f"Green camera shoot clicked - Shutter: {shutter0}ms")
        
        # Show progress indication
        # self.status_label.setText("Capturing photo...")
        QApplication.processEvents()  # Update UI
        # print(["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '0', shutter0])
        print(type(shutter0))
        try:
            # Use timeout to prevent hanging
            print('before subprocess call')
            result = subprocess.run(
                ["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', '0', shutter0],
                check=True,
                timeout=30,  # 30 second timeout
                capture_output=True,
                text=True
            )
            #self.status_label.setText("Photo captured successfully")
            # Automatically load the most recent green camera photo
            loaded_file = self.load_recent_image(camera_id=0)
            if loaded_file:
                print(f"Successfully loaded: {loaded_file}")
            else:
                print("Photo captured but could not load image")
                #self.status_label.setText("Photo captured but could not load image")
        except subprocess.TimeoutExpired:
            #self.status_label.setText("Photo capture timed out")
            print(f"Photo capture timed out")
        except subprocess.CalledProcessError as e:
            #self.status_label.setText("Photo capture failed")
            print(f"Error: {e.stderr}")
        except Exception as e:
            #self.status_label.setText("Unexpected error")
            print(f"Unexpected error: {e}")
            
    def on_uv_shoot(self):
        """Handle UV camera shoot"""
        shutter = self.spinBox_uv_shutter.value()
        print(f"UV camera shoot clicked - Shutter: {shutter}ms")
        
    def on_both_shoot(self):
        """Handle both cameras shoot"""
        green_shutter = self.spinBox_green_shutter.value()
        uv_shutter = self.spinBox_uv_shutter.value()
        print(f"Both cameras shoot clicked - Green: {green_shutter}ms, UV: {uv_shutter}ms")
    
    
    # Calibration functions
    def on_start_calibration(self):
        """Start calibration scan sequence"""
        print('hia?')
        try:
            # Initialize reconstruction array
            
            stepsize= 3
            print('hia?2')
            
            # Get calibration parameters
            min_pan = -18#self.spinBox_min_pan.value() * -1
            max_pan = 18#self.spinBox_max_pan.value() * -1
            min_tilt = 0#self.spinBox_min_tilt.value()
            max_tilt = 40#self.spinBox_max_tilt.value()
            self.isi = self.spinBox_isi_caliScan.value()
            
            # Generate scan coordinates
            self.hh_coordinates = np.arange(min_pan,max_pan+stepsize,stepsize)
            self.vv_coordinates = np.arange(min_tilt,max_tilt+stepsize,stepsize)
            self.recon = np.zeros((len(self.hh_coordinates)*len(self.vv_coordinates),3))
            print(self.hh_coordinates,self.vv_coordinates,self.recon.shape)
            # #np.random.rand(len(self.vv_coordinates), len(self.hh_coordinates), 3)  # RGB format
            
            # Create scan positions
            ## from upper-left to lower-right
            self.scan_pos = [(hh, vv) for vv in self.vv_coordinates[::-1] for hh in self.hh_coordinates[::-1]]
            # # self.scan_pos_inds = [(h_id, v_id) for h_id in COORDINATE_inds for v_id in COORDINATE_inds]
            #print(self.scan_pos)
            
            #print(f"Starting calibration scan with {len(self.scan_pos)} positions")
            #print(f"Pan range: {min_pan} to {max_pan}, Tilt range: {min_tilt} to {max_tilt}")
            
            # # Execute scan sequence
            # #for i, (pos, pos_ids) in enumerate(zip(self.scan_pos, self.scan_pos_inds)):
            for i, pos in enumerate(self.scan_pos):
                pan, tilt = pos
                # pan_id, tilt_id = pos_ids
                
                #print(f"Position {i+1}/{len(self.scan_pos)}: Pan={pan}, Tilt={tilt}")
                
                # Move to position
                self.motor_controller.move_to(pan, tilt)
                time.sleep(self.isi)
                
                # Perform calibration scan and store result
                rgb_value = self.on_cali_scan()
                print(f'COLOR:{rgb_value}')
                #self.recon[tilt_id, pan_id] = rgb_value
                self.recon[i] = rgb_value
                
                # Update progress (you could add a progress bar later)
                print(f"Completed: RGB={rgb_value}")
            self.recon = self.recon.reshape((len(self.vv_coordinates),len(self.hh_coordinates),3))    
            print("Calibration scan completed!")
            self.display_reconstruction()
            self.save_calibration()
        except Exception as e:
            print(f"Calibration error: {str(e)}")
    
   
    def on_cali_scan(self):
        """Perform a single calibration scan and return RGB classification"""
        try:
            int_time = self.spinBox_int_caliScan.value()
            
            # Perform scan
            result = self.spec_controller.scan(int_time)
            
            if result['success']:
                # Extract data
                wavelengths = result['wavelengths']
                intensity = result['intensity']
                
                # Find peak wavelength
                max_nm = wavelengths[np.argmax(intensity)]
                print(f'Max intensity at: {max_nm:.1f} nm')
                
                # Classify based on peak wavelength
                if max_nm > 550:
                    return np.array([1.0, 0.0, 0.0])  # Red 576
                elif max_nm < 550 and max_nm > 420:
                    return np.array([0.0, 1.0, 0.0])  # Green 483
                else:
                    return np.array([0.0, 0.0, 1.0])  # Blue 403nm
                    
            else:
                print(f"Scan failed: {result['error']}")
                return np.array([0.0, 0.0, 0.0])  # Default to black on failure
                
        except Exception as e:
            print(f"Calibration scan error: {str(e)}")
            return np.array([0.0, 0.0, 0.0])  # Default to black on error
    
    def display_reconstruction(self):
        """Display reconstruction using direct QPixmap creation"""
        try:
            if not hasattr(self, 'recon'):
                print("No reconstruction data available")
                return None
            
            # Convert numpy array to QImage
            height, width, channels = self.recon.shape
            
            # Ensure data is in correct format (0-255 uint8)
            recon_uint8 = (self.recon * 255).astype(np.uint8)
            
            # Create QImage
            bytes_per_line = 3 * width
            q_image = QImage(recon_uint8.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            # Scale to fit
            pixmap = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Display in QGraphicsView
            scene = self.graphicsView_recon_scan.scene()
            if scene is None:
                scene = QGraphicsScene()
                self.graphicsView_recon_scan.setScene(scene)
            else:
                scene.clear()
            
            scene.addPixmap(pixmap)
            self.graphicsView_recon_scan.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
            print("Reconstruction displayed successfully")
            return True
            
        except Exception as e:
            print(f"Error displaying reconstruction: {e}")
            return None
    def save_calibration(self):
        """Save calibration data to file"""
        if hasattr(self, 'recon'):
            np.save(os.path.join(CALI_PATH,'calibration_reconstruction.npy'), self.recon)
            print("Calibration data saved!")

        def on_stop_calibration(self):
            """Stop calibration"""
            print("Stop calibration clicked")
    def on_stop_calibration(self):
        """Stop calibration"""
        print("Stop calibration clicked")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())