import seabreeze.spectrometers as sb

import os
import math
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
DATA_PATH = os.path.join(SCAM_PATH, 'data')
DARK_NOISES_PATH = os.path.join(SCAM_PATH, "dark_noises")

# Configurable sleep duration (in seconds)
SLEEP_DURATION = 0.2
MIN_INT_TIME = 0.01  # Minimum integration time in milliseconds

# List available spectrometer devices
devices = sb.list_devices()
print("Available devices:", devices)
spec = sb.Spectrometer.from_serial_number("S03615")#STS-UV-L-100-400-SMA
print ('spectrometer serial number: ',spec.serial_number)

# Ensure the spectrometer is in DARK
response = input("Ensure the telescope is covered before proceeding. Type 'Y' to confirm: ")
if response.strip().upper() != 'Y':
    print("Aborted.")
    exit(1)

# Define integration times (in milliseconds)
integration_times_ms = [ii for ii in range(1,1001)]
# [ii for ii in range(1000,10000,50)]
# [ii for ii in range(10000,100000, 100)]
measured_int_times = np.load(os.path.join(DATA_PATH, 'all_int_times.npy'))
## MEASURED in ms
# np.linspace(0.01, 0.99, 99)
# [100, 200, 300, 400, 500, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000]
# [10, 20, 40, 80]
# [100, 200, 300, 400, 500, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 5000, 8000, 10000]

# Create output directory
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = DARK_NOISES_PATH
os.makedirs(output_dir, exist_ok=True)

# Record dark noise for each integration time
for int_time in integration_times_ms:
    if int_time not in measured_int_times:
        # Validate integration time before setting it
        if MIN_INT_TIME <= int_time :
            print(f"Measuring dark noise at {int_time} ms...")
            spec.integration_time_micros(int_time*1e3)
        else:
            print(f"Integration time {int_time} ms is out of range. Skipping...")
            continue

        # Allow time to settle
        time.sleep(SLEEP_DURATION) # unit in seconds
        # Take multiple scans and average them
        num_scans = 10
        spectra = []
        for _ in range(num_scans):
            wavelengths, intensity = spec.spectrum()
            spectra.append(intensity)
            time.sleep(2)
        dark_avg = np.mean(spectra, axis=0)

        # Save data
        np.savez(os.path.join(output_dir, f'dark_{int_time}ms.npz'),
                wavelength=wavelengths, dark_avg=dark_avg)

        # Plot
        plt.figure()
        plt.plot(wavelengths, dark_avg)
        plt.title(f'Dark Noise at {int_time} ms')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (counts)')
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, f'dark_{int_time}ms.png'))
        plt.close()

print("Dark noise measurements complete. Data saved in:", output_dir)


from sts_utils import extract_integration_times
output_file = os.path.join(DATA_PATH,'all_int_times.npy')

# Run the function
extract_integration_times(DARK_NOISES_PATH, output_file)