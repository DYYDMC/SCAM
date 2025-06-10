import numpy as np
import json
import time
from datetime import datetime
import os

class ScanDataHandler:
    def __init__(self):
        self.scan_data = {}
        self.photo_times = []
        
    def add_scan(self, coordinates, wavelengths, intensities):
        timestamp = time.time()
        self.scan_data[timestamp] = {
            'coor': coordinates,
            'wavelengths': wavelengths.tolist() if isinstance(wavelengths, np.ndarray) else wavelengths,
            'intensities': intensities.tolist() if isinstance(intensities, np.ndarray) else intensities
        }
        
    def add_photo_time(self, timestamp):
        self.photo_times.append(timestamp)
        
    def save_data(self, filename=None):
        if filename is None:
            filename = f"scan_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        data = {
            'scans': self.scan_data,
            'photo_times': self.photo_times
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f)
            
        return filename