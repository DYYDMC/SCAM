import cv2
import numpy as np
import os
import sys
import glob
from ChessBoardCornerDetector import ChessboardCornerDetector

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM0_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam0","cam0_roi.npy")
CAM1_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam1","cam1_roi.npy")

CAM0_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam0")
CAM1_VIG_PATH =os.path.join(SCAM_PATH, "vignette", "cam1")

# input a single image path (cam0_xyz.jpg or cam1_xyz.jpg)
img_folder = sys.argv[1]
vigged_folder = os.path.join(img_folder, "cropped_vig_corrected")
cornered_folder = os.path.join(img_folder, "cropped_corners")
os.makedirs(vigged_folder, exist_ok=True)
os.makedirs(cornered_folder, exist_ok=True)

detector = ChessboardCornerDetector(pattern_size=(8,5))
print("\n=== FULL CAMERA CALIBRATION ===")
if os.path.exists(img_folder):
    # Perform calibration
    success = detector.calibrate_camera(vigged_folder,cornered_folder, "*.jpg")
    
    if success:
        # Save calibration data
        output_calibration_path = os.path.join(img_folder,"my_camera_calibration.npz")
        print(output_calibration_path)
        detector.save_calibration_data(output_calibration_path)
        print(f"Saved camera calibration data to: {output_calibration_path}")