import numpy as np
import time
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon
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
        """Handle move to position and then scans"""
        try:
            # First move to position
            pan = self.spinBox_pan.value()
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