import time as t
from datetime import datetime, time, timedelta
import subprocess
import seabreeze.spectrometers as sb
import os
import numpy as np
from ESP32_utils import initialize_connection, move_to_esp32, close_connection

RP_USER = "ydeng"
RP_IP = "192.168.2.126"# "192.168.50.100"
REMOTE_SCRIPT = "/home/ydeng/GitHub/rgbCamera/bash_scripts/small_h264still_generators.sh"


# === CONFIGURABLE PARAMETERS ===
start_time_str = "12:48"
end_time_str = "19:20"
interval_minutes = 30
# Convert time strings to time objects
start_time = datetime.strptime(start_time_str, "%H:%M").time()
end_time = datetime.strptime(end_time_str, "%H:%M").time()


def hourly_task():
    current_time = datetime.now().strftime("%H_%M_%S")
    remote_command = f"mkdir -p /home/ydeng/GitHub/rgbCamera/data/cali_cam_scan/tt{current_time}"
    ssh_command = ["ssh", f"{RP_USER}@{RP_IP}", remote_command]

    try:
        subprocess.run(ssh_command, check=True)
        print(f"Folder '{current_time}' created successfully on {RP_IP}")
    except subprocess.CalledProcessError as e:
        print("Failed to create folder:", e)

    # connect to the spectrometer
    devices = sb.list_devices()
    print(devices)
    spec = sb.Spectrometer.from_serial_number("S03615")
    spec.integration_time_micros(int(.1 * 1e6))  # 100ms

    origx, origy = (-1, -10)
    cam_positions = [(origx + 71 - 20 * ii, origy) for ii in range(7)][::-1]
    print(cam_positions)
    scan_positions = np.load('./deltas_29032025.npy')
    print(scan_positions)
    outputs = np.zeros((len(cam_positions), len(scan_positions), 1024))

    for cc, cp in enumerate(cam_positions):
        origx, origy = cp
        move_to_esp32(origx, origy)
        t.sleep(.5)
        print('Taking photo')
        subprocess.run(["ssh", f"{RP_USER}@{RP_IP}", f"{REMOTE_SCRIPT} {cc}"])

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
            t.sleep(60)
            print('PAUSE')
            if ii%2==0:
                move_to_esp32(0, 10)
            else:
                move_to_esp32(0, -10)

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

