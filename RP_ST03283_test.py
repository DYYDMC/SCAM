import time
import matplotlib.pyplot as plt
import numpy as np
import seabreeze
seabreeze.use("pyseabreeze")

import seabreeze.spectrometers as sb
devices = sb.list_devices() 
print(f"Found {len(devices)} device(s): {devices}")
spec = sb.Spectrometer(devices[0])

# micro_time = 5*1e6

# spec.integration_time_micros(micro_time)
# start = time.perf_counter()
# _,ints = spec.spectrum()
# elapsed = time.perf_counter() - start
# print(f"Took {elapsed:.6f} seconds")

micro_time = 3*1e6
start = time.perf_counter()

spec.integration_time_micros(micro_time)
nm,ints = spec.spectrum()
elapsed = time.perf_counter() - start
# plt.plot(nm,ints)
# # plt.plot(nm,ints-dark_)
# plt.vlines(nm[np.argmax(ints)],np.min(ints),np.max(ints),color='r',label=nm[np.argmax(ints)])
# plt.title('quick_test'.format(micro_time/1e3))
# # plt.ylim(np.min(ints),np.max(ints))
# plt.legend()
print(f"Took {elapsed:.6f} seconds")