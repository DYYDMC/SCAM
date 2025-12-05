import glob
import cv2
import numpy as np
import os
import sys

def apply_roi_to_image(img_path, roi, output_path=None):
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
roi_npy_path = sys.argv[1]
roi = np.load(roi_npy_path)
img_path = sys.argv[2]
print('roi npy file:', roi_npy_path)
print('img_path:', img_path)

to_crops = glob.glob(img_path+'*.jpg')
    
output_path = img_path + '/cropped/'
print('output_path:', output_path)
os.makedirs(output_path, exist_ok=True)
for tt,tc in enumerate(to_crops):
    print(tc.split('/')[-1])
    print(f'Processing {tt+1}/{len(to_crops)}: {tc}')
    if 'cam0' in tc:
        _ = apply_roi_to_image(tc,roi,output_path+'cam0_cropped_'+tc.split('/')[-1])
    if 'cam1' in tc:
        _ = apply_roi_to_image(tc,roi,output_path+'cam1_cropped_'+tc.split('/')[-1])
        