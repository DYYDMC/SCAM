import os
import sys
import time
import numpy as np
import subprocess
from datetime import datetime
import seabreeze.spectrometers as sb

# --- Configuration ---
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
PATHS = {
    'roi': os.path.join(SCAM_PATH, "cam_roi"),
    'scan': os.path.join(SCAM_PATH, "spec_scan"),
    'gui': os.path.join(SCAM_PATH, "GUI"),
    'rs': os.path.join(SCAM_PATH, 'rs_motor'),
    'cali': os.path.join(SCAM_PATH, 'cali'),
    'dark': os.path.join(SCAM_PATH, "dark_noises"),
    'photo_script': os.path.join(SCAM_PATH, 'cali', "cali_cam_take_photo.sh"),
    'data': os.path.join(SCAM_PATH, 'data')
}

sys.path.insert(1, PATHS['rs'])
from ESP32_light_utils import initialize_connection, move_to_esp32, close_connection
sys.path.insert(1,PATHS['scan'])
from sts_utils import get_optimal_integration_time
all_int_times = np.load(os.path.join(PATHS['data'], 'all_int_times.npy'))
# --- Calibration Parameters ---
SERIAL_NUMBER = 'S03615'
INT_TIME_MS = 500  # in milliseconds default
STEP_DEG = 2
V_RANGE = (-24, 24)
H_RANGE = (-34, 34)

# --- Initialization ---
initialize_connection()
spec = sb.Spectrometer.from_serial_number(SERIAL_NUMBER)
spec.integration_time_micros(INT_TIME_MS * 1000)

wavelengths, _ = spec.spectrum()
dark_noise_file = os.path.join(PATHS['dark'], f'dark_{INT_TIME_MS}ms.npz')
if not os.path.exists(dark_noise_file):
    raise FileNotFoundError(f"Dark noise file missing: {dark_noise_file}")
dark_noise = np.load(dark_noise_file)['dark_avg']

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = os.path.join(PATHS['scan'], timestamp)
os.makedirs(output_dir, exist_ok=True)

scan_data = {
    'serial_number': SERIAL_NUMBER,
    'integration_time': INT_TIME_MS * 1000,
    'wavelengths': wavelengths,
    'v_min': V_RANGE[0],
    'v_max': V_RANGE[1],
    'h_min': H_RANGE[0],
    'h_max': H_RANGE[1],
    'step_size': STEP_DEG,
    'scan_positions' : [(0,v) for v in [V_RANGE[0],0,V_RANGE[1]]],
    'measurements': {},
}
print(scan_data['scan_positions'])
# --- Scan Loop ---
try:
    for scan_pos in scan_data['scan_positions']:
        h,v = scan_pos
        move_to_esp32(h, v)
        time.sleep(0.5)
        tmp_int_t = get_optimal_integration_time(all_int_times, spec)
        time.sleep(0.5)
        _, spectrum = spec.spectrum()
        corrected = spectrum - dark_noise
        scan_data['measurements'][(h, v)] = {}
        scan_data['measurements'][(h, v)]['ts'] = int(time.time())
        scan_data['measurements'][(h, v)]['clean'] = corrected
        scan_data['measurements'][(h, v)]['int_t'] = tmp_int_t
        time.sleep(0.5)

finally:
    close_connection()
    spec.close()

# --- Save Output ---
output_file = os.path.join(output_dir, 'scan.npz')
np.savez_compressed(output_file, **scan_data)