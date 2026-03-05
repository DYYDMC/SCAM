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
# all_raws=glob.glob(os.path.join(target_folder,'*.raw'))
print(target_dir)
#print(os.path.join(one_scan_path,'SCAM*/'))
# print(os.path.join(one_scan_path,'ONE_SCAM*/'))
# target_dir = glob.glob(os.path.join(one_scan_path,'SCAM*/'))
# target_dir = glob.glob(os.path.join(one_scan_path,'ONE_SCAM*/'))
#for dir in target_dir:
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
        'int_t': scan_dict['metadata']['integration_time_ms'],
        'loc':(scan_dict['motor_pan'], scan_dict['motor_tilt']),
        'unix_ts': int(dt.timestamp()),
        'year': dt.year,
        'month': dt.month,
        'day': dt.day,
        'hour': dt.hour,
        'minute': dt.minute,
        'second': dt.second
    }
    data.append(row)
df = pd.DataFrame(data)
df.to_pickle(target_dir + 'scan_data.pkl')
        
        