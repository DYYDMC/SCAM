import seabreeze.spectrometers as sb

import os
import math
import numpy as np
import matplotlib.pyplot as plt
import time
import datetime

# set graphics to be plotted inline if in Jupyter
try:
    get_ipython().run_line_magic('matplotlib', 'inline')
except:
    pass

# List available spectrometer devices
devices = sb.list_devices()
print("Available devices:", devices)

spec = sb.Spectrometer.from_serial_number("S03615")#STS-UV-L-100-400-SMA
# serial number
print ('spectrometer serial number: ',spec.serial_number)

response = input("CHECK IF THE TELESCOPE IS COVERED (type Y to continue): ")
if response.strip().upper() != 'Y':
    print("Aborted.")
    exit(1)

# Define integration times (in milliseconds)
integration_times_ms = [10, 20, 40, 80]#, 100, 200, 300, 400, 500, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 5000, 8000, 10000]

# Create output directory
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = f'../dark_noises/'
os.makedirs(output_dir, exist_ok=True)

# Record dark noise for each integration time
for int_time in integration_times_ms:
    print(f"Measuring dark noise at {int_time} ms...")
    spec.integration_time_micros(int_time * 1000)

    # Allow time to settle
    print('start sleeping')
    time.sleep(.5) # unit in seconds
    print("AWAKE!")


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


