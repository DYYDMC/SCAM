import cv2
import numpy as np
import os
import sys
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

CAM0_VIG_MASK = os.path.join(SCAM_PATH, "vignette", "cam0","vignette_mask.npy")
CAM1_VIG_MASK = os.path.join(SCAM_PATH, "vignette", "cam1","vignette_mask.npy")

# input a single image path (cam0_xyz.jpg or cam1_xyz.jpg)
img_path = sys.argv[1]

dir_path = os.path.dirname(img_path)
fname = os.path.basename(img_path)

output_fname = fname.replace('.jpg', '_cropped.jpg')
output_path = os.path.join(dir_path,output_fname)

print("input img path:", img_path)
print('output_path:', output_path)

if 'cam0' in img_path:
    ifCrop = apply_roi_to_image(img_path,CAM0_ROI_NPY,output_path)
if 'cam1' in img_path:
    ifCrop = apply_roi_to_image(img_path,CAM1_ROI_NPY,output_path)

if ifCrop is not None:
    print("Cropping successful.")
    
    # continue to vignetting correction
    vignette_mask = np.load(CAM0_VIG_MASK) if 'cam0' in img_path else np.load(CAM1_VIG_MASK)
    imgfloat32 = ifCrop.astype(np.float32)
    corrected_img = cv2.divide(imgfloat32, vignette_mask)
    corrected_img_clipped = np.clip(corrected_img, 0, 255).astype(np.uint8)
    vig_output_fname = fname.replace('.jpg', '_cropped_vig_corrected.jpg')
    vig_output_path = os.path.join(dir_path,vig_output_fname)
    cv2.imwrite(vig_output_path, corrected_img_clipped)
    print(f"Saved vignette corrected image: {vig_output_path}")
    
    # continue to corner detection
    detector = ChessboardCornerDetector(pattern_size=(8,5))
    single_image_path = vig_output_path
    print(f"\nFinding corners in cropped image: {single_image_path}")
    output_fname = fname.replace('.jpg', '_cropped_corners.jpg')
    cornered_output_path = os.path.join(dir_path,output_fname)
    corners = detector.detect_corners_single_image(single_image_path,cornered_output_path,show_result=False)
    
else:
    print("Cropping failed.")