import os
import seabreeze.spectrometers as sb
import numpy as np
import sys

# print("HA")
spec = sb.Spectrometer.from_serial_number("S03615")#STS-UV-L-100-400-SMA
# serial number
print ('spectrometer serial number: ',spec.serial_number)
int_time = int(sys.argv[1]) if len(sys.argv) > 1 else 100

# print("HERE")
spec.integration_time_micros(int_time * 1000)
wavelengths, intensity = spec.spectrum()

dark_noise = np.load(f"/Users/eulerlab/Github/SCAM/dark_noises/dark_{int_time}ms.npz")['dark_avg']

output_dir = f'/Users/eulerlab/Github/SCAM/GUI'
print(os.path.join(output_dir, 'scan_output.npz'))
# print(os.getcwd())
np.savez(os.path.join(output_dir, 'scan_output.npz'),
             wavelength=wavelengths, dark_avg=intensity-dark_noise)