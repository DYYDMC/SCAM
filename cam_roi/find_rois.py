import cv2
import numpy as np
import os
import sys
def get_roi(img_path, pixelThr=30):
    """
    Calculate the region of interest (ROI) for a given image.

    Args:
        img_path (str): The file path to the image.
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
    
    colorCh = 0  # Default to UV channel
    if "cam0" in img_path:
        colorCh = 1  # Green channel for cam0 img
    if "cam1" in img_path:
        colorCh = 0  # UV channel for cam1 img
    # Set default thresholds if not provided
    if pixelThr is None:
        print('hia')
        pixelThr = 30 if colorCh == 0 else 100  # UV=30, Green=100
    
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
    print(x_start_norm, y_start_norm, width_norm, height_norm)
    return (x_start_norm, y_start_norm, width_norm, height_norm)

def main(roi_jpg_path,roi_threshold):
    roi = get_roi(roi_jpg_path,roi_threshold)
    output_roi_path =roi_jpg_path.replace('.jpg', '_fin.npy')
    output_roi_threshold_path =roi_jpg_path.replace('.jpg', '_threshold_fin.npy')
    np.save(output_roi_path,roi)
    np.save(output_roi_threshold_path,roi_threshold)

roi_jpg_path = sys.argv[1]
roi_threshold = int(sys.argv[2])
print(roi_threshold)
# roi_jpg_path = '/home/ydeng/Github/SCAM/GUI/cam0/cam0_0.jpg'
print('roi jpg file:', roi_jpg_path)
if __name__ == "__main__":
    main(roi_jpg_path,roi_threshold)
        
        