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

CAM0_VIG_MASK = os.path.join(SCAM_PATH, "vignette", "cam0","vignette_mask.npy")
CAM1_VIG_MASK = os.path.join(SCAM_PATH, "vignette", "cam1","vignette_mask.npy")

# input a single image path (cam0_xyz.jpg or cam1_xyz.jpg)
img_folder = sys.argv[1]
cropped_folder = os.path.join(img_folder, "cropped")
vigged_folder = os.path.join(img_folder, "cropped_vig_corrected")
cornered_folder = os.path.join(img_folder, "cropped_corners")
os.makedirs(cropped_folder, exist_ok=True)
os.makedirs(vigged_folder, exist_ok=True)
os.makedirs(cornered_folder, exist_ok=True)

img_paths = glob.glob(os.path.join(img_folder, "*.jpg"))
# crop and de-vignette each image, with intermediate outputs saved
for img_path in img_paths:
    fname = os.path.basename(img_path)

    cropped_fname = fname.replace('.jpg', '_cropped.jpg')
    vigged_fname = fname.replace('.jpg', '_cropped_vig_corrected.jpg')
    
    cropped = apply_roi_to_image(img_path,
                                 CAM0_ROI_NPY if 'cam0' in img_path else CAM1_ROI_NPY,
                                 os.path.join(cropped_folder, cropped_fname))
    if cropped is not None:
        print("Cropping successful.")
        
        # continue to vignetting correction
        vignette_mask = np.load(CAM0_VIG_MASK) if 'cam0' in img_path else np.load(CAM1_VIG_MASK)
        imgfloat32 = cropped.astype(np.float32)
        corrected_img = cv2.divide(imgfloat32, vignette_mask)
        corrected_img_clipped = np.clip(corrected_img, 0, 255).astype(np.uint8)
        vigged_output_path = os.path.join(vigged_folder, vigged_fname)
        cv2.imwrite(vigged_output_path, corrected_img_clipped)
        print(f"Saved vignette corrected image: {vigged_output_path}")

# detect corners for all vig-corrected images
detector = ChessboardCornerDetector(pattern_size=(8,5))
print("\n=== FULL CAMERA CALIBRATION ===")
if os.path.exists(vigged_folder):
    # Perform calibration
    success = detector.calibrate_camera(vigged_folder,cornered_folder, "*.jpg")
    
    if success:
        # Save calibration data
        output_calibration_path = os.path.join(img_folder,"my_camera_calibration.npz")
        print(output_calibration_path)
        detector.save_calibration_data(output_calibration_path)
        print(f"Saved camera calibration data to: {output_calibration_path}")