import glob
import cv2
import numpy as np
import os
import sys


def get_roi(img_path, colorCh, pixelThr=None):
    """
    Calculate the region of interest (ROI) for a given image.

    Args:
        img_path (str): The file path to the image.
        colorCh (int): The color channel (cv2.imread mapping) 0=blue, 1=green, 2=red
        pixelThr (int, optional): Pixel threshold. If None, uses default based on colorCh.

    Returns:
        tuple: (x_start_norm, y_start_norm, width_norm, height_norm) representing the ROI.
    """
    image_array = cv2.imread(img_path)
    if image_array is None:
        print(f"Error: Could not read image {img_path}")
        return None
    
    nrows, ncols, ncolor = image_array.shape
    print(f"Image shape: {image_array.shape}")
    
    # Set default thresholds if not provided
    if pixelThr is None:
        pixelThr = 30 if colorCh == 0 else 100  # UV=30, Green=100
    
    # Flip for UV camera
    if colorCh == 0:  # UV
        image_array = np.flip(image_array, axis=1)
    
    # Get the specific color channel
    channel_data = image_array[:, :, colorCh]
    
    print(f"Color channel {colorCh}, threshold: {pixelThr}")
    print(f"Channel stats - Min: {np.min(channel_data)}, Max: {np.max(channel_data)}, Mean: {np.mean(channel_data):.2f}")
    
    # Find start and end columns (x-axis)
    col_max = np.max(channel_data, axis=0)  # Max value in each column
    valid_cols = np.where(col_max > pixelThr)[0]
    
    if len(valid_cols) == 0:
        print("Warning: No columns exceed threshold, using full width")
        x_start, x_end = 0, ncols
    else:
        x_start = valid_cols[0]  # First column above threshold
        x_end = valid_cols[-1]   # Last column above threshold
    
    # Find start and end rows (y-axis)
    row_max = np.max(channel_data, axis=1)  # Max value in each row
    valid_rows = np.where(row_max > pixelThr)[0]
    
    if len(valid_rows) == 0:
        print("Warning: No rows exceed threshold, using full height")
        y_start, y_end = 0, nrows
    else:
        y_start = valid_rows[0]  # First row above threshold
        y_end = valid_rows[-1]   # Last row above threshold
    
    # Convert to normalized coordinates
    x_start_norm = x_start / ncols
    y_start_norm = y_start / nrows
    width_norm = (x_end - x_start) / ncols
    height_norm = (y_end - y_start) / nrows
    
    print(f"ROI - X: {x_start}-{x_end} ({width_norm:.3f} width), "
          f"Y: {y_start}-{y_end} ({height_norm:.3f} height)")
    
    return (x_start_norm, y_start_norm, width_norm, height_norm)

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
        img = img[:,:,1]
    if 'cam1' in img_path:
        img = img[:,:,0]
    
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
img_path = sys.argv[1]
print('img_path:', img_path)
print(type(img_path))
to_crops = glob.glob(img_path+'*.jpg')
print(len(to_crops))
if 'cam0' in img_path:
    roi = np.load('./cam0_roi.npy')
    
if 'cam1' in img_path:
    roi = np.load('./cam1_roi.npy')
    
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
        