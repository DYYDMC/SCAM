import numpy as np
import sys
import os
sys.path.insert(0, '/Users/dengyuyao/Github/SCAM/spec_scan')
from sts_utils import extract_integration_times

# ha = np.load('/Users/dengyuyao/Github/SCAM/data/all_int_times.npy')
# print(ha)
# print(type(ha[0]))
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
DARK_NOISES_PATH = os.path.join(SCAM_PATH,'dark_noises')
DATA_PATH = os.path.join(SCAM_PATH, 'data')
dark_noises_folder = "/Users/dengyuyao/Github/SCAM/dark_noises"
output_file = os.path.join(DATA_PATH,'all_int_times.npy')

# Run the function
extract_integration_times(DARK_NOISES_PATH, output_file)