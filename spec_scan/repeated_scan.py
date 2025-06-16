import time as t
from datetime import datetime, time, timedelta
import subprocess
import seabreeze.spectrometers as sb
import os
import numpy as np

import sys
import fcntl


# Parse CLI arguments

twitch_up = tuple(map(int, sys.argv[2].split(','))) if len(sys.argv) > 2 else (0,10)
twitch_down = tuple(map(int, sys.argv[3].split(','))) if len(sys.argv) > 3 else (0,-10)

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")

CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
RS_MOTOR_PATH = os.path.join(SCAM_PATH,'rs_motor')
sys.path.insert(1,RS_MOTOR_PATH)
from ESP32_light_utils import initialize_connection, move_to_esp32, close_connection

SPEC_SCAM_PATH = os.path.join(SCAM_PATH, 'spec_scan')




# === CONFIGURABLE PARAMETERS ===
start_time_str = "12:48"
end_time_str = "19:20"
interval_minutes = 10
# Convert time strings to time objects
start_time = datetime.strptime(start_time_str, "%H:%M").time()
end_time = datetime.strptime(end_time_str, "%H:%M").time()


def hourly_task():
    with open(LOCK_FILE_PATH, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Spectrometer is in use. Skipping this task.")
            return
            current_time = datetime.now().strftime("%H_%M_%S")
            target_path = os.path.join(AUTO_SCAM_DATA_PATH, f"tt{current_time}")
            os.makedirs(target_path, exist_ok=True)
            print(f"Folder '{target_path}' created successfully.")

            # connect to the spectrometer
            devices = sb.list_devices()
            print(devices)
            spec = sb.Spectrometer.from_serial_number("S03615")
            spec.integration_time_micros(int(.1 * 1e6))  # 100ms

            origx, origy = (-1, -10)
            cam_positions = [(origx + 71 - 20 * ii, origy) for ii in range(7)][::-1]
            print(cam_positions)
            scan_positions = np.load(os.path.join(SPEC_SCAM_PATH,'deltas_29032025.npy'))
            print(scan_positions)
            outputs = np.zeros((len(cam_positions), len(scan_positions), 1024))

            for cc, cp in enumerate(cam_positions):
                origx, origy = cp
                move_to_esp32(origx, origy)
                t.sleep(.5)
                print('Taking photo')
                # subprocess.run(["ssh", f"{RP_USER}@{RP_IP}", f"{REMOTE_SCRIPT} {cc}"])
                subprocess.run([REMOTE_SCRIPT, str(cc), shutter0, shutter1])

                for ss, sp in enumerate(scan_positions):
                    delta_x, delta_y = sp
                    move_to_esp32(origx + delta_x, origy + delta_y)
                    t.sleep(.8)
                    _, outputs[cc, ss] = spec.spectrum()
                    t.sleep(1)

            np.save(f'../data/cam_scan/spectralScan_{current_time}.npy', outputs)

# === MAIN SCHEDULING LOOP ===
if __name__ == "__main__":
    initialize_connection()
    try:
        move_to_esp32(0,0)
        print('physically align the machine gun set up')
        t.sleep(5)
        last_task_time = datetime.now() - timedelta(minutes=interval_minutes)
        hourly_task()
        for ii in range(interval_minutes):
            t.sleep(2)# 60 second
            print('PAUSE')
            if ii % 2 == 0:
                move_to_esp32(*twitch_up)
            else:
                move_to_esp32(*twitch_down)


        # while True:
        #     print('LOOPING')
        #     now = datetime.now()
        #     current_time = now.time()

        #     # Check if it's time to run the main task
        #     if now - last_task_time >= timedelta(minutes=interval_minutes):
        #         if start_time <= current_time < end_time:
        #             print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled task...")
        #             hourly_task()
        #         else:
        #             print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Outside active window ({start_time_str}–{end_time_str}). Skipping task.")
        #         last_task_time = now
        #     # KEEP-ALIVE ACTION: move servo slightly every X seconds
        #     move_to_esp32(0, 10)   # small twitch
        #     t.sleep(60)
        #     move_to_esp32(0, 0)
        #     t.sleep(60)           # repeat every 10 seconds
    finally:
        close_connection()
        print('Connection closed')


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
        optimal_time = get_optimal_integration_time(all_int_times, spec)
        for h in range(H_RANGE[1], H_RANGE[0] - 1, -STEP_DEG):
            move_to_esp32(h, v)
            time.sleep(0.5)
            get_optimal_integration_time
            _, spectrum = spec.spectrum()
            corrected = spectrum - dark_noise
            scan_data['measurements'][(h, v)] = {}
            scan_data['measurements'][(h, v)]['ts'] = int(time.time())
            scan_data['measurements'][(h, v)]['clean'] = corrected
            time.sleep(0.5)

finally:
    close_connection()
    spec.close()

# --- Save Output ---
output_file = os.path.join(output_dir, 'scan.npz')
np.savez_compressed(output_file, **scan_data)