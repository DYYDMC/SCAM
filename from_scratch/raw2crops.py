import cv2
import numpy as np
import os
import sys
import glob
from ChessBoardCornerDetector import ChessboardCornerDetector

# function to apply ROI
def apply_roi_to_image(img_path, roi_npy_path, output_path):
    """
    Apply ROI to an image and optionally save the result.
    
    Args:
        img_path (str): Path to the image
        roi (tuple): (x_start_norm, y_start_norm, width_norm, height_norm)
        output_path (str, optional): Path to save cropped image
    
    Returns:
        numpy.ndarray: Cropped image
    """
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not read image {img_path}")
        return None
    if 'cam0' in img_path:
        img = img[:,:,1] # B G R, take G channel
    if 'cam1' in img_path:
        img = img[:,:,0] # B G R, take B channel
    
    nrows, ncols = img.shape[:2]
    roi = np.load(roi_npy_path)
    x_start_norm, y_start_norm, width_norm, height_norm = roi
    
    # Convert normalized coordinates to pixel coordinates
    x_start = int(x_start_norm * ncols)
    y_start = int(y_start_norm * nrows)
    width = int(width_norm * ncols)
    height = int(height_norm * nrows)
    
    # Ensure coordinates are within bounds
    x_start = max(0, min(x_start, ncols-1))
    y_start = max(0, min(y_start, nrows-1))
    width = max(1, min(width, ncols - x_start))
    height = max(1, min(height, nrows - y_start))
    
    # Crop the image
    cropped = img[y_start:y_start+height, x_start:x_start+width]
    
    if output_path:
        cv2.imwrite(output_path, cropped)
        print(f"Saved cropped image: {output_path} (Size: {cropped.shape[1]}x{cropped.shape[0]})")
    
    return cropped
    
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM0_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam0","cam0_roi.npy")
CAM1_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam1","cam1_roi.npy")

# input a single image path (cam0_xyz.jpg or cam1_xyz.jpg)
img_folder = sys.argv[1]
cropped_folder = os.path.join(img_folder, "cropped")
os.makedirs(cropped_folder, exist_ok=True)


img_paths = glob.glob(os.path.join(img_folder, "*.jpg"))
# crop and de-vignette each image, with intermediate outputs saved
for img_path in img_paths:
    fname = os.path.basename(img_path)

    cropped_fname = fname.replace('.jpg', '_cropped.jpg')
    
    cropped_output_path = os.path.join(cropped_folder, cropped_fname)
    print(cropped_output_path)
    
    cropped = apply_roi_to_image(img_path,
                                 CAM0_ROI_NPY if 'cam0' in img_path else CAM1_ROI_NPY,
                                 cropped_output_path)
    print(cropped.shape)
    break