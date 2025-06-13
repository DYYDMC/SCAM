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
    'photo_script': os.path.join(SCAM_PATH, 'cali', "cali_cam_take_photo.sh")
}

sys.path.insert(1, PATHS['rs'])
from ESP32_light_utils import initialize_connection, move_to_esp32, close_connection

# --- Calibration Parameters ---
SERIAL_NUMBER = 'S03615'
INT_TIME_MS = 200  # in milliseconds
STEP_DEG = 2
V_RANGE = (-24, 36)
H_RANGE = (-40, 40)
SHUTTER_SETTINGS = {"0": "1000000", "1": "1000000"}

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
output_dir = os.path.join(PATHS['cali'], timestamp)
os.makedirs(output_dir, exist_ok=True)

cali_data = {
    'serial_number': SERIAL_NUMBER,
    'integration_time': INT_TIME_MS * 1000,
    'wavelengths': wavelengths,
    'measurements': {},
    'v_min': V_RANGE[0],
    'v_max': V_RANGE[1],
    'h_min': H_RANGE[0],
    'h_max': H_RANGE[1],
    'step_size': STEP_DEG,
}

# --- Scan Loop ---
try:
    for v in range(V_RANGE[0], V_RANGE[1] + 1, STEP_DEG):
        for h in range(H_RANGE[1], H_RANGE[0] - 1, -STEP_DEG):
            move_to_esp32(h, v)
            time.sleep(0.5)
            _, spectrum = spec.spectrum()
            corrected = spectrum - dark_noise
            cali_data['measurements'][(h, v)] = corrected
            time.sleep(0.5)

            if h == 0:
                for cam_id, shutter in SHUTTER_SETTINGS.items():
                    proc = subprocess.run(
                        [PATHS['photo_script'], "capture_still", output_dir, str(v), cam_id, shutter],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    if proc.returncode != 0:
                        print(f"Photo capture failed at v={v}, cam={cam_id}: {proc.stderr.decode()}")

finally:
    close_connection()
    spec.close()

# --- Save Output ---
output_file = os.path.join(output_dir, 'spec_calibration.npz')
np.savez_compressed(output_file, **cali_data)
