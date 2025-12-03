import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import sys
from spherical_controller import ChessboardCornerDetector


# define paths
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM_ROI_PATH = os.path.join(SCAM_PATH, "cam_roi")
SPHERICAL_CAM0_PATH = os.path.join(CAM_ROI_PATH, "cam0_chess_newROI_30112025")
SPHERICAL_CAM1_PATH = os.path.join(CAM_ROI_PATH, "cam1_chess_newROI_30112025")
# CALI_PATH = os.path.join(SCAM_PATH,"cali")
# SPEC_SCAN_PATH = os.path.join(SCAM_PATH, "spec_scan")
# GUI_PATH = os.path.join(SCAM_PATH, "GUI")
# GUI_CAM0 = os.path.join(GUI_PATH,'cam0')
# GUI_CAM1 = os.path.join(GUI_PATH,'cam1')
# RS_PATH = os.path.join(SCAM_PATH,'rs_motor')
# STP_PATH =os.path.join(SCAM_PATH,'stepper')


def main(crop_path):
    """
    Main function demonstrating the complete workflow
    """
    # Initialize detector with 9 rows x 6 columns pattern (6,9 inner corners)
    detector = ChessboardCornerDetector(pattern_size=(8,5))
    
    # Load existing calibration data
    print("\n=== LOADING EXISTING CALIBRATION ===")
    if 'cam0' in crop_path:
        spherical_cali_path = os.path.join(SPHERICAL_CAM0_PATH,"my_camera_calibration.npz")
    if 'cam1' in crop_path:
        spherical_cali_path =  os.path.join(SPHERICAL_CAM1_PATH,"my_camera_calibration.npz")
    if os.path.exists(spherical_cali_path):
        detector.load_calibration_data(spherical_cali_path)
        # Use loaded calibration to undistort an image
    to_undistort = glob.glob(crop_path+'*.jpg')
    for img_path in to_undistort:
        if os.path.exists(img_path):
            print(f"\nUndistorting image: {img_path}")
            output_path = img_path.replace('.jpg', '_undistorted.jpg')
            detector.undistort_image(img_path, output_path)
        else:
            print(f"Test image {img_path} does not exist.")
        
crop_path = sys.argv[1]+'cropped/'
print('crop_path:', crop_path)   
if __name__ == "__main__":
    main(crop_path)