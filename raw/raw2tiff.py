import sys
sys.path.insert(1,'/Users/dengyuyao/Github/SCAM/raw')
from raw_prepro import *
import glob
import tifffile as tiff
import os
## take path input from terminal

target_folder=str(sys.argv[1])
all_raws=glob.glob(os.path.join(target_folder,'*.raw'))

for raw in all_raws:
    raw2d = cut_raw_black_lines(raw)
    if 'cam1' in raw:
        B2d = extract_B_raw(raw2d)
        tiff.imwrite(raw.replace('.raw','_B.tiff')
                     ,B2d,compression=None)
    if 'cam0' in raw:
        G2d=extract_G_raw(raw2d)
        tiff.imwrite(raw.replace('.raw','_G.tiff'),G2d,compression=None)
