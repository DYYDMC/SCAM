import cv2
import numpy as np
import os
import sys

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM0_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam0")
CAM1_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam1")


def img_correct_vignette(img_path, out_path):
    if 'cam0' in img_path:
        roi = np.load(os.path.join(CAM0_VIG_PATH, "threshold_vig_roi.npy"))  # [y_min, y_max, x_min, x_max]
        vignette_mask_cropped = np.load(os.path.join(CAM0_VIG_PATH,"roi_cropped_vig_mask.npy")) 
    if 'cam1' in img_path:
        roi = np.load(os.path.join(CAM1_VIG_PATH, "threshold_vig_roi.npy"))  # [y_min, y_max, x_min, x_max]
        vignette_mask_cropped = np.load(os.path.join(CAM1_VIG_PATH,"roi_cropped_vig_mask.npy")) 
    
    print(roi,vignette_mask_cropped.shape)
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
    
## test code
# img_path = sys.argv[1]
# output_path = img_path.replace('.jpg', '_vig_corrected.jpg')
# img_correct_vignette(img_path,output_path)