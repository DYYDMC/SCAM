# function to read roi tuples
# is it necessary?
import sys
import numpy as np

def read_roi(file_path):
    roi = np.load(file_path)
    print(','.join(map(str, roi)))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_roi.py <path_to_npy_file>")
        sys.exit(1)
    read_roi(sys.argv[1])