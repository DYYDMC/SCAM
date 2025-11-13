# Change from PyQt5 to PySide6
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import loadUiType

# Load the .ui file directly - NO CONVERSION NEEDED!
Ui_MainWindow, QtBaseClass = loadUiType('/home/ydeng/Github/SCAM/GUI/SCAM_gui.ui')



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
    
    # OneScan functions
    def on_spec_scan(self):
        """Handle spectral scan button"""
        int_time = self.spinBox_int_oneScan.value()
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