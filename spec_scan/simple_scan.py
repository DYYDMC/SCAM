import os
import seabreeze.spectrometers as sb
import numpy as np
import sys
import time
import json
from datetime import datetime

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
GUI_PATH = os.path.join(SCAM_PATH, 'GUI')
DARK_NOISES_PATH = os.path.join(SCAM_PATH, "dark_noises")

def load_dark_noise(int_time):
    """Load dark noise for given integration time"""
    dark_file = os.path.join(DARK_NOISES_PATH, f"dark_{int_time}ms.npz")
    if not os.path.exists(dark_file):
        raise FileNotFoundError(f"Dark noise file not found for {int_time}ms")
    return np.load(dark_file)['dark_avg']

def save_scan_data(wavelengths, intensity, dark_corrected, metadata=None):
    """Save scan data with optional metadata"""
    timestamp = datetime.now().isoformat()
    output_file = os.path.join(GUI_PATH, 'scan_output.npz')
    
    save_dict = {
        'wavelength': wavelengths,
        'intensity': intensity,  # Raw intensity
        'dark_avg': dark_corrected,  # Dark-corrected intensity
        'timestamp': timestamp
    }
    
    if metadata:
        save_dict['metadata'] = metadata
    
    np.savez(output_file, **save_dict)
    
    # Also save as JSON for easier human reading
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

def main():
    try:
        # Get integration time from command line
        int_time = float(sys.argv[1]) if len(sys.argv) > 1 else 100
        
        # Initialize spectrometer
        spec = sb.Spectrometer.from_serial_number("S03615")
        print(f'Spectrometer serial number: {spec.serial_number}')
        
        # Set integration time
        spec.integration_time_micros(int_time * 1000)
        
        # Get spectrum
        wavelengths, intensity = spec.spectrum()
        print('the maximum of measured raw values: ',np.max(intensity))
        
        # Load and apply dark correction
        try:
            dark_noise = load_dark_noise(int_time)
            dark_corrected = intensity - dark_noise
        except Exception as e:
            print(f"Warning: Could not apply dark correction - {str(e)}")
            dark_corrected = intensity  # Use raw data if dark correction fails
        
        # Prepare metadata
        metadata = {
            'integration_time_ms': int_time,
            'serial_number': spec.serial_number,
            'dark_correction_applied': 'dark_noise' in locals()
        }
        
        # Save data
        save_scan_data(wavelengths, intensity, dark_corrected, metadata)
        
        return True
        
    except Exception as e:
        print(f"Error during scan: {str(e)}", file=sys.stderr)
        return False
    finally:
        # Ensure spectrometer is closed
        if 'spec' in locals():
            spec.close()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)