# import numpy as np
# ha = np.load('../cam/cam_shutter_ag.npy')
# print(ha)
# )
# import sys
import os
# sys.path.insert(0, '/Users/dengyuyao/Github/SCAM/spec_scan')
# from sts_utils import extract_integration_times

# # ha = np.load('/Users/dengyuyao/Github/SCAM/data/all_int_times.npy')
# # print(ha)
# # print(type(ha[0]))
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
# DARK_NOISES_PATH = os.path.join(SCAM_PATH,'dark_noises')
DATA_PATH = os.path.join(SCAM_PATH, 'data')
# dark_noises_folder = "/Users/dengyuyao/Github/SCAM/dark_noises"
# output_file = os.path.join(DATA_PATH,'all_int_times.npy')

# # Run the function
# extract_integration_times(DARK_NOISES_PATH, output_file)

import pickle
# Load from pickle file
with open(os.path.join(DATA_PATH,'TEST_pos2shutters.pkl'), 'rb') as f:
    loaded_dict = pickle.load(f)
keys =list(loaded_dict.keys())
print(keys)
print(loaded_dict[keys[0]])
print(loaded_dict[keys[1]])
# print(loaded_dict.keys())
# print(loaded_dict.items())
