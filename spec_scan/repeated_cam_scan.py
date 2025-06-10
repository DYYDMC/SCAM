import time as t
from datetime import datetime, time, timedelta
import subprocess
import seabreeze.spectrometers as sb
import os
import numpy as np


import sys
import fcntl


# Parse CLI arguments
interval_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
twitch_up = tuple(map(int, sys.argv[2].split(','))) if len(sys.argv) > 2 else (0,10)
twitch_down = tuple(map(int, sys.argv[3].split(','))) if len(sys.argv) > 3 else (0,-10)
shutter0 = sys.argv[4] if len(sys.argv) > 4 else "100000"
shutter1 = sys.argv[5] if len(sys.argv) > 5 else "1000000"

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")

CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
RS_MOTOR_PATH = os.path.join(SCAM_PATH,'rs_motor')
# print(os.listdir(CAM_ROI_PATH))
sys.path.insert(1,RS_MOTOR_PATH)
from ESP32_light_utils import initialize_connection, move_to_esp32, close_connection

REMOTE_SCRIPT = os.path.join(CAM_ROI_PATH, "cam_take_photo.sh")
AUTO_SCAM_DATA_PATH = os.path.join(SCAM_PATH, "auto_scam_data")
SPEC_SCAM_PATH = os.path.join(SCAM_PATH, 'spec_scan')
LOCK_FILE_PATH = os.path.join(SCAM_PATH, "spec.lock")




# === CONFIGURABLE PARAMETERS ===
start_time_str = "12:48"
end_time_str = "19:20"
interval_minutes = 30
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

