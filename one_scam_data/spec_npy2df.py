import numpy as np
import pandas as pd
from datetime import datetime
import glob
import os
import sys

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
one_scan_path=os.path.join(SCAM_PATH, "one_scam_data")
target_dir=str(sys.argv[1])

print(target_dir)

scan_dir=os.path.join(target_dir,'scan_data')
print(f'turn all the npy files under {scan_dir} to a .pkl')
all_npys = glob.glob(scan_dir + '/*.npy')

data=[]
for npy_file in all_npys:
    scan_dict = np.load(npy_file, allow_pickle=True).item()
    dt=datetime.strptime(scan_dict['ts'],'%Y%m%d_%H%M%S')
    row={
        'wavelength': scan_dict['wavelengths'],
        'spectrum': scan_dict['intensity'],
        'dark_corr':scan_dict['metadata']['dark_correction_applied'],
        'int_t': np.uint32(scan_dict['metadata']['integration_time_ms']),
        'loc':(scan_dict['motor_pan'], scan_dict['motor_tilt']),
        'unix_ts': int(dt.timestamp()),
        'year': np.uint16(dt.year),
        'month': np.uint8(dt.month),
        'day': np.uint8(dt.day),
        'hour': np.uint8(dt.hour),
        'minute': np.uint8(dt.minute),
        'second': np.uint8(dt.second)
    }
    data.append(row)
df = pd.DataFrame(data)
out_pkl = os.path.join(target_dir, 'scan_data2.pkl')

df.to_pickle(out_pkl)

print(f"saved: {out_pkl}")

        
        
