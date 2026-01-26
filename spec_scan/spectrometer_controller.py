#!/usr/bin/env python3
import seabreeze
seabreeze.use('pyseabreeze')  # Use the Python backend
import seabreeze.spectrometers as sb

import os
import numpy as np
import json
from datetime import datetime

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
GUI_PATH = os.path.join(SCAM_PATH, 'GUI')
DARK_NOISES_PATH = os.path.join(SCAM_PATH, "dark_noises")

class SpectrometerController:
    def __init__(self):
        self.spec = None
        self.is_connected = False
    
    def connect(self):
        """Initialize and connect to spectrometer"""
        try:
            if self.spec is None:
                devices = sb.list_devices()
                print(f"Found {len(devices)} device(s): {devices}")
                #self.spec = sb.Spectrometer.from_serial_number("S03615") # STS-UV
                # self.spec = sb.Spectrometer.from_serial_number("USB2+F02461")
                #self.spec = sb.Spectrometer.from_serial_number("S15434") # STS-VIS
                #self.spec = sb.Spectrometer.from_serial_number("ST03283") # ST-UV
                self.spec = sb.Spectrometer(devices[0])
                self.is_connected = True
                print(f'Spectrometer connected: {self.spec.serial_number}')
                return True
            return self.is_connected
        except Exception as e:
            print(f"Connection error: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Close spectrometer connection"""
        if self.spec is not None:
            self.spec.close()
            self.spec = None
            self.is_connected = False
            print("Spectrometer disconnected")
    
    def load_dark_noise(self, int_time):
        """Load dark noise for given integration time"""
        dark_file = os.path.join(DARK_NOISES_PATH, f"dark_{int_time}ms.npz")
        if not os.path.exists(dark_file):
            raise FileNotFoundError(f"Dark noise file not found for {int_time}ms")
        return np.load(dark_file)['dark_avg']
    
    def save_scan_data(self, wavelengths, intensity, dark_corrected, metadata=None):
        """Save scan data with optional metadata"""
        timestamp = datetime.now().isoformat()
        output_file = os.path.join(GUI_PATH, 'scan_output.npz')
        
        save_dict = {
            'wavelength': wavelengths,
            'intensity': intensity,
            'dark_avg': dark_corrected,
            'timestamp': timestamp
        }
        
        if metadata:
            save_dict['metadata'] = metadata
        
        np.savez(output_file, **save_dict)
        
        # Also save as JSON
        json_data = {
            'timestamp': timestamp,
            'wavelengths': wavelengths.tolist(),
            'intensity': intensity.tolist(),
            'dark_corrected': dark_corrected.tolist()
        }
        if metadata:
            json_data['metadata'] = metadata
            
        with open(os.path.join(GUI_PATH, 'scan_output.json'), 'w') as f:
            json.dump(json_data, f)
    
    def scan(self, int_time=100):
        """Perform a single scan"""
        if not self.is_connected or self.spec is None:
            if not self.connect():
                raise ConnectionError("Spectrometer not connected")
        
        try:
            # Set integration time from ms -> micro-second
            self.spec.integration_time_micros(int_time * 1000)
            print(f"Integration time set to {int_time} ms")
            
            # Get spectrum
            wavelengths, intensity = self.spec.spectrum()
            print('Maximum of measured raw values:', np.max(intensity))
            
            # Load and apply dark correction
            try:
                dark_noise = self.load_dark_noise(int_time)
                dark_corrected = intensity - dark_noise
                dark_correction_applied = True
            except Exception as e:
                print(f"Warning: Could not apply dark correction - {str(e)}")
                dark_corrected = intensity
                dark_correction_applied = False
            print('i m here')
            # Prepare metadata
            metadata = {
                'integration_time_ms': int_time,
                'serial_number': self.spec.serial_number,
                'dark_correction_applied': dark_correction_applied
            }
            
            # Save data
            # self.save_scan_data(wavelengths, intensity, dark_corrected, metadata)
            
            return {
                'wavelengths': wavelengths,
                'intensity': intensity,
                'dark_corrected': dark_corrected,
                'metadata': metadata,
                'success': True
            }
            
        except Exception as e:
            print(f"Scan error: {str(e)}")
            return {'success': False, 'error': str(e)}