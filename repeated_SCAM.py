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
    'cam': os.path.join(SCAM_PATH, 'cam'),
    'data': os.path.join(SCAM_PATH, 'data')
}

sys.path.insert(1, PATHS['rs'])
from ESP32_light_utils import initialize_connection, move_to_esp32, close_connection
sys.path.insert(1,PATHS['scan'])
from sts_utils import get_optimal_integration_time
all_int_times = np.load(os.path.join(PATHS['data'], 'all_int_times.npy'))
# --- Calibration Parameters ---
SERIAL_NUMBER = 'S03615'
INT_TIME_MS = 100  # in milliseconds init integration time
STEP_DEG = 2
V_RANGE = (-24, 24)
H_RANGE = (-34, 34)
num_scan_perPos = 1
num_iterations = 1  # number of iterations for 3-pos-scan

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
output_dir = os.path.join(PATHS['data'], timestamp)
os.makedirs(output_dir, exist_ok=True)

scan_data = {
    'serial_number': SERIAL_NUMBER,
    'wavelengths': wavelengths,
    'v_min': V_RANGE[0],
    'v_max': V_RANGE[1],
    'h_min': H_RANGE[0],
    'h_max': H_RANGE[1],
    'step_size': STEP_DEG,
    'num_iterations': num_iterations,
    'scan_positions' : [(0,v) for v in [V_RANGE[0],0,V_RANGE[1]]],
    'num_scan_perPos': num_scan_perPos,
    'measurements': {},
}
print(scan_data['scan_positions'])
# --- Scan Loop ---
try:
    previous_int_t = INT_TIME_MS * 1000  # Start with the default integration time
    for ii in range(num_iterations):  # Loop through the specified number of iterations
        for scan_pos in scan_data['scan_positions']:
            h, v = scan_pos
            move_to_esp32(h, v)
            time.sleep(2)
            tmp_int_t = get_optimal_integration_time(all_int_times, spec, previous_ints=previous_int_t)
            previous_int_t = tmp_int_t  # Use the current integration time for the next iteration
            time.sleep(0.5)
            spec.integration_time_micros(tmp_int_t * 1000)
            
            for scan_num in range(num_scan_perPos):
                # take a measurement
                print(f"Taking measurement at position (h={h}, v={v}), scan number {scan_num + 1}/{num_scan_perPos}")
                _, spectrum = spec.spectrum()
                corrected = spectrum - dark_noise
                
                # store the measurement for the current timestamp and position
                # easier modification for one position multiple scans : same pos different timestamps
                ts = int(time.time())
                scan_data['measurements'][ts] = {}
                scan_data['measurements'][ts]['pos']=(h,v)
                scan_data['measurements'][ts]['clean'] = corrected
                scan_data['measurements'][ts]['int_t'] = tmp_int_t
                time.sleep(0.5)

            ## start to take camera img
            # load the cam_shutter_again
            
            cam_shutter_ag= np.load(os.path.join(PATHS['cam'],'cam_shutter_ag.npy'))
            os.makedirs(output_dir, exist_ok=True)
            for cam in [0,1]:
                shutter = cam_shutter_ag[cam,1]
                analoggain = cam_shutter_ag[cam,2]
                img_filename = os.path.join(output_dir, f"cam{cam}_shutter{shutter}_ag{analoggain}_iter{ii}_h{h}v{v}.jpg")
                subprocess.run(["bash", os.path.join(PATHS['cam'],"cam_take_photo.sh"), img_filename,
                                str(cam), str(shutter), str(analoggain)], check=True)
        

finally:
    close_connection()
    spec.close()

# --- Save Output ---
output_file = os.path.join(output_dir, 'scan.npz')
np.savez_compressed(output_file, **scan_data)