import numpy as np
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import loadUiType

# Load the .ui file directly - NO CONVERSION NEEDED!
Ui_MainWindow, QtBaseClass = loadUiType('/home/ydeng/Github/SCAM/GUI/SCAM_gui.ui')

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(project_root)

# load SCAN-related functions
from spec_scan.spectrometer_controller import SpectrometerController

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Pass 'self' as the argument
        
        # Set window icon programmatically
        icon_path = os.path.join(os.path.dirname(__file__), 'SCAM_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon not found at: {icon_path}")
        
        ## instantiate the SpectrometerController
        self.spec_controller = SpectrometerController()
        
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
    
    def load_plot(self, scan_data_path=None):
        """Load and display spectrometer scan plot in QGraphicsView"""
        try:
            # Use default path if none provided
            if scan_data_path is None:
                GUI_PATH = os.path.join(project_root, "GUI")
                scan_data_path = os.path.join(GUI_PATH, "scan_output.npz")
            
            # Load the data
            data = np.load(scan_data_path)
            wavelengths = data["wavelength"]
            intensity = data["dark_avg"]
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
            ax.plot(wavelengths, intensity, 'b-', linewidth=1)
            ax.set_title("Spectrometer Output")
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Intensity")
            ax.grid(True, alpha=0.3)
            
            # Convert matplotlib figure to QPixmap
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # Create QPixmap from the buffer
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue(), 'PNG')
            
            # Clear the scene and add the pixmap
            scene = self.graphicsView_scan_oneScan.scene()
            if scene is None:
                scene = QGraphicsScene()
                self.graphicsView_scan_oneScan.setScene(scene)
            else:
                scene.clear()
            
            scene.addPixmap(pixmap)
            self.graphicsView_scan_oneScan.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
            # Clean up
            plt.close(fig)
            buf.close()
            
        except Exception as e:
            print(f"Error loading spectrum: {str(e)}")
            # Display error message in the graphics view
            scene = self.graphicsView_scan_oneScan.scene()
            if scene is None:
                scene = QGraphicsScene()
                self.graphicsView_scan_oneScan.setScene(scene)
            else:
                scene.clear()
            
            error_text = scene.addText(f"Error loading spectrum:\n{str(e)}")
            self.graphicsView_scan_oneScan.fitInView(error_text.sceneBoundingRect(), Qt.KeepAspectRatio)
            
    # OneScan functions
    def on_spec_scan(self):
        """Handle spectral scan button"""
        try:
            # Get integration time from your GUI input
            int_time = int(self.spinBox_int_oneScan.value())
            
            # Perform scan
            result = self.spec_controller.scan(int_time)
            print('Scan result:', result)
            
            if result['success']:
                print('Loading plot...')
                self.load_plot()
            else:
                print(f"Scan failed: {result['error']}")
                
        except Exception as e:
            print(f"Scan error: {str(e)}")
        
        pan = self.spinBox_pan.value()
        tilt = self.spinBox_tilt.value()
        print(f"Scan clicked - Integration: {int_time}ms, Pan: {pan}, Tilt: {tilt}")
    
        
    def on_move_scan(self):
        """Handle move to position"""
        pan = self.spinBox_pan.value()
        tilt = self.spinBox_tilt.value()
        print(f"Move clicked - Pan: {pan}, Tilt: {tilt}")
    
    # Camera functions
    def on_green_shoot(self):
        """Handle green camera shoot"""
        shutter = self.spinBox_green_shutter.value()
        print(f"Green camera shoot clicked - Shutter: {shutter}ms")
        
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
        """Start calibration"""
        min_pan = self.spinBox_min_pan.value()
        max_pan = self.spinBox_max_pan.value()
        min_tilt = self.spinBox_min_tilt.value()
        max_tilt = self.spinBox_max_tilt.value()
        int_time = self.spinBox_int_caliScan.value()
        interval = self.spinBox_isi_caliScan.value()
        
        print(f"Start calibration clicked")
        print(f"  Pan range: {min_pan} to {max_pan}")
        print(f"  Tilt range: {min_tilt} to {max_tilt}")
        print(f"  Integration: {int_time}ms, Interval: {interval}ms")
        
    def on_stop_calibration(self):
        """Stop calibration"""
        print("Stop calibration clicked")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())