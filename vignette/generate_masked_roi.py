import numpy as np
import os 

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")

CAM0_VIG =os.path.join(SCAM_PATH, "vignette", "cam0")
CAM1_VIG =os.path.join(SCAM_PATH, "vignette", "cam1")

for mask in [os.path.join(CAM0_VIG,'vignette_mask.npy'),os.path.join(CAM1_VIG,'vignette_mask.npy')]:
    print(mask)
    mask_full = np.load(mask)  # 2104x2069 float32, 0.007~1

    thr = 0.1  # 有效区域阈值
    valid = mask_full > thr
    ys, xs = np.where(valid)

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    threshold_vig_roi = np.array([y_min, y_max, x_min, x_max])
    roi_fname = os.path.basename(mask).replace('vignette_mask.npy','threshold_vig_roi.npy')
    roi_path = os.path.join(os.path.dirname(mask),roi_fname)
    np.save(roi_path, threshold_vig_roi)

    # 裁剪后的 roi_cropped_vig_mask
    roi_cropped_vig_mask = mask_full[y_min:y_max+1, x_min:x_max+1]
    cropped_fname = os.path.basename(mask).replace('vignette_mask.npy','roi_cropped_vig_mask.npy')
    cropped_path =  os.path.join(os.path.dirname(mask),cropped_fname)
    np.save(cropped_path, roi_cropped_vig_mask)

    print("Mask:", mask)
    print("ROI:", y_min, y_max, x_min, x_max)
    print("cropped shape:", roi_cropped_vig_mask.shape)
    print("Saved ROI to:", roi_path)
    print("Saved cropped mask to:", cropped_path)
    print("-----")
