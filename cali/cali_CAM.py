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
STEP_DEG = 2
V_RANGE = (-24, 36)
H_RANGE = (-35, 35)
SHUTTER_SETTINGS = {"0": "1000000", "1": "1000000"}

# --- Initialization ---
initialize_connection()

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = os.path.join(PATHS['cali'], timestamp)
os.makedirs(output_dir, exist_ok=True)

# --- Scan Loop ---
try:
    for v in range(V_RANGE[0], V_RANGE[1] + 1, STEP_DEG):
        for h in range(H_RANGE[1], H_RANGE[0] - 1, -STEP_DEG):
            move_to_esp32(h, v)
            time.sleep(0.5)
            if h == -1:
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
