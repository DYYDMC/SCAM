import os
from pathlib import Path
import cv2
import numpy as np
import glob
import sys
# generate vignette template from images of uniformly illuminated white wall

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
    
    return cropped

HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM0_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam0","cam0_roi.npy")
CAM1_ROI_NPY = os.path.join(SCAM_PATH, "roi", "cam1","cam1_roi.npy")

img_folder = sys.argv[1]
print('img_folder:', img_folder)

vignette_mask = None
for img_path in glob.glob(img_folder+'*.jpg'):
    print(img_path)
    fname = os.path.basename(img_path)
    output_fname = fname.replace('.jpg', '_cropped.jpg')
    output_path = os.path.join(img_folder,output_fname)   
   
    img = cv2.imread(img_path)
    if 'cam0' in img_path:
        cropped = apply_roi_to_image(img_path,CAM0_ROI_NPY,output_path)
    if 'cam1' in img_path:
        cropped = apply_roi_to_image(img_path,CAM1_ROI_NPY,output_path)
    
    if vignette_mask is None:
        vignette_mask = cropped.astype(np.float32)
    else:
        vignette_mask += cropped.astype(np.float32)
num_samples = len(glob.glob(img_folder+'*.jpg'))
vignette_mask /= num_samples
# 归一化模板（防止除以0）
vignette_mask = vignette_mask / np.max(vignette_mask)
cv2.imwrite(os.path.join(img_folder,"vignette_mask.png"), vignette_mask * 255)
np.save(os.path.join(img_folder,"vignette_mask.npy"), vignette_mask)
