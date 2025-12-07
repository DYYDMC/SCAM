import cv2
import numpy as np
import os
import sys
import glob
from ChessBoardCornerDetector import ChessboardCornerDetector
def img_correct_vignette(img_path, out_path):
    if 'cam0' in img_path:
        print('G ch')
        roi = np.load(os.path.join(CAM0_VIG_PATH, "threshold_vig_roi.npy"))  # [y_min, y_max, x_min, x_max]
        vignette_mask_cropped = np.load(os.path.join(CAM0_VIG_PATH,"roi_cropped_vig_mask.npy")) 
    if 'cam1' in img_path:
        print('UV ch')
        roi = np.load(os.path.join(CAM1_VIG_PATH, "threshold_vig_roi.npy"))  # [y_min, y_max, x_min, x_max]
        vignette_mask_cropped = np.load(os.path.join(CAM1_VIG_PATH,"roi_cropped_vig_mask.npy")) 
    
    
    y_min, y_max, x_min, x_max = roi.astype(int)   
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)          # H x W x C

    # 1. 用同一 ROI 裁剪图像
    cropped = img[y_min:y_max+1, x_min:x_max+1]               # Hc x Wc x C
    # 2. 检查尺寸是否匹配
    Hc, Wc = cropped.shape[:2]
    assert vignette_mask_cropped.shape == (Hc, Wc)

    # 3. 去暗角（限制最小增益）
    imgfloat32 = cropped.astype(np.float32)
    safe_mask = np.clip(vignette_mask_cropped, 0.3, 1.0).astype(np.float32)  # Hc x Wc

    corrected = imgfloat32 / safe_mask
    corrected_clipped = np.clip(corrected, 0, 255).astype(np.uint8)

    cv2.imwrite(out_path, corrected_clipped)
    return True


    
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")

CAM0_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam0")
CAM1_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam1")

# input a single image path (cam0_xyz.jpg or cam1_xyz.jpg)
img_folder = sys.argv[1]
cropped_folder = os.path.join(img_folder, "cropped")
vigged_folder = os.path.join(img_folder, "cropped_vig_corrected")
os.makedirs(cropped_folder, exist_ok=True)
os.makedirs(vigged_folder, exist_ok=True)

img_paths = glob.glob(os.path.join(cropped_folder, "*.jpg"))
# crop and de-vignette each image, with intermediate outputs saved
for img_path in img_paths:
    fname = os.path.basename(img_path)
    vigged_fname = fname.replace('.jpg', '_cropped_vig_corrected.jpg')
    vigged_output_path = os.path.join(vigged_folder, vigged_fname)
    print('input for vignette ',img_path )
    vig_corrected = img_correct_vignette(img_path,vigged_output_path)
        