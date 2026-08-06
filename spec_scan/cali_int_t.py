import time
from spectrometer_controller import SpectrometerController
spec_controller = SpectrometerController()
spec_controller.connect()
import numpy as np
import pickle

used_int_t_for_scan = np.load('./all_darknoise_int.npy')
print(np.unique(used_int_t_for_scan).shape)

dict_all_darknoise_int_t_to_ms = {}
for int_t in used_int_t_for_scan:
    #start = time.perf_counter()
    dict_all_darknoise_int_t_to_ms[int_t] = spec_controller.scan(int_t)
    #elapsed = time.perf_counter() - start
    #print(int_t,elapsed)
    # dict_int_t_2ms[int_t] = elapsed
    # print(f"Integration time {int_t} ms took {elapsed:.6f} seconds")

with open('./dict_all_darknoise_int_t_to_ms.pkl', 'wb') as f:
    pickle.dump(dict_all_darknoise_int_t_to_ms, f)  
#print(dict_all_darknoise_int_t_to_ms)