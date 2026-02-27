import subprocess
import os
import sys
import glob
import numpy as np
import cv2
from datetime import datetime
import pickle

# Define paths globally
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CALI_PATH = os.path.join(SCAM_PATH,"cali")
CAM_PATH = os.path.join(SCAM_PATH, 'cam')
CAM0_ROI_NPY = os.path.join(SCAM_PATH,'roi','cam0','cam0_roi.npy')
CAM1_ROI_NPY = os.path.join(SCAM_PATH,'roi','cam1','cam1_roi.npy')
DATA_PATH = os.path.join(SCAM_PATH, 'data')

# function to apply ROI
def apply_roi_to_image(gray, roi_npy_path, output_path=None):
    """
    Apply ROI to an image and optionally save the result.
    
    Args:
        gray (str): single channel img (raw, full resolution)
        roi (tuple): (x_start_norm, y_start_norm, width_norm, height_norm)
        output_path (str, optional): Path to save cropped image
    
    Returns:
        numpy.ndarray: Cropped image
    """
    nrows, ncols = gray.shape[:2]
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
    cropped = gray[y_start:y_start+height, x_start:x_start+width]
    
    if output_path:
        cv2.imwrite(output_path, cropped)
        print(f"Saved cropped image: {output_path} (Size: {cropped.shape[1]}x{cropped.shape[0]})")
    
    return cropped

def call_bash_script(camera_id, shutter, analoggain, output_dir, img_idx=0):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Calling bash script for camera {camera_id} with shutter {shutter} and gain {analoggain}")
    print('cmd:',["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', str(camera_id), shutter, analoggain,output_dir,str(img_idx)])
    try:
        # Use timeout to prevent hanging
        print('before subprocess call')
        result = subprocess.run(
            ["/bin/bash", os.path.join(CALI_PATH, 'cali_cam_take_photo.sh'), 'capture_still', str(camera_id), shutter, analoggain,output_dir,str(img_idx)],
            check=True,
            timeout=30,  # 30 second timeout
            capture_output=True,
            text=True
        )
    except subprocess.TimeoutExpired:
        #self.status_label.setText("Photo capture timed out")
        print(f"Photo capture timed out")
    except subprocess.CalledProcessError as e:
        #self.status_label.setText("Photo capture failed")
        print(f"Error: {e.stderr}")
    except Exception as e:
        #self.status_label.setText("Unexpected error")
        print(f"Unexpected error: {e}")
    pattern = f"*cam{camera_id}*.jpg"
    try:
        search_path = os.path.join(output_dir, pattern)
        files = glob.glob(search_path)
        if not files:
            return None
        latest_path = max(files, key=os.path.getmtime)
        return os.path.basename(latest_path)
    except Exception:
        return None

def analyze_image(img_filename):
    # Open the image
    img = cv2.imread(img_filename)  # Read the image using OpenCV
    
    if 'cam0' in img_filename:
        gray = img[:,:,1] # G 
    if 'cam1' in img_filename: 
        gray = img[:,:,1] # Blue
        
    # crop it according to the CAM_roi
    cropped = apply_roi_to_image(gray,
                                 CAM0_ROI_NPY if 'cam0' in img_filename else CAM1_ROI_NPY,
                                 output_path=None)
    # # calculate mean brightness
    # brightness = np.mean(cropped)


    # # Define thresholds for overexposure and underexposure
    # overexposed_threshold = 240  # Example threshold for overexposure
    underexposed_threshold = 50  # Example threshold for underexposure
    
    if np.max(cropped) == 255:
        return "overexposed"
    elif np.max(cropped) < underexposed_threshold:
        return "underexposed"
    else:
        return "ok"
# Core search function
def adaptive_search_exposure(camera_id, output_dir, initial_tuple=(1.12,100000)):
    print("Starting adaptive search for camera", camera_id)
    os.makedirs(output_dir, exist_ok=True)
    print("output dir:", output_dir)
    print("initial guess:", initial_tuple)
    min_shutter, max_shutter, step_shutter = int(999), int(1033e3), int(1e4)
    min_again, max_again, step_again = 1.12, 8.0, 0.4
    search_range_shutter = list(range(min_shutter, max_shutter, step_shutter))
    search_range_again = np.arange(min_again, max_again, step_again).round(1).tolist()

    camera_id = int(camera_id)
    output_dir = str(output_dir)
    ag, shutter = initial_tuple
    results = []

    def update_range(search_range, val, direction):
        if direction == "increase":
            return [x for x in search_range if x > val]
        elif direction == "decrease":
            return [x for x in search_range if x < val]
        else:
            return search_range

    stack = [(ag, shutter)]

    while stack:
        current_ag, current_shutter = stack.pop()
        img_filename = call_bash_script(camera_id, current_shutter, current_ag, output_dir)
        result = analyze_image(img_filename)
        print(result,(current_ag, current_shutter))

        if result == "ok":
            results.append((current_ag, current_shutter))
            break
        else:
            os.remove(img_filename)
            direction_change = "increase" if result == "underexposed" else "decrease"
            new_range_again = update_range(search_range_again, current_ag, direction_change)
            new_range_shutter = update_range(search_range_shutter, current_shutter, direction_change)
            
            # priority to shutter, then again
            for new_ag in reversed(new_range_again):
                stack.append((new_ag, current_shutter))
            for new_shutter in reversed(new_range_shutter):
                stack.append((current_ag, new_shutter))
                
    return results

def main(camera_ids, shutter_range, again_range, output_dir, initial_guesses=None):
    os.makedirs(output_dir, exist_ok=True)
    results = {0: None, 1: None}

    results[0] = adaptive_search_exposure(0,output_dir, initial_guesses[0])
    results[1] = adaptive_search_exposure(1,output_dir, initial_guesses[1])
    print(f"Final results: {results}")

    # Save results as a dictionary in a .pkl file
    local_save_path = os.path.join(output_dir, 'cam_ag_shutter.pkl')
    global_save_path = os.path.join(DATA_PATH, 'cam_ag_shutter.pkl')

    # Save one in the cam_path under the timestamp folder
    with open(local_save_path, 'wb') as f:
        pickle.dump(results, f)

    # Save/overwrite one in the data folder for global access
    with open(global_save_path, 'wb') as f:
        pickle.dump(results, f)

    return results
if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(CAM_PATH, timestamp)
    camera_ids = [0, 1]
    
    # Global search ranges
    min_shutter, max_shutter, step_shutter = int(33e3), int(1033e3), int(50e3)
    min_again, max_again, step_again = 1.2, 8.1, 0.4
    search_range_shutter = list(range(int(33e3), int(1033e3), int(50e3)))
    search_range_again = np.arange(min_again, max_again, step_again).round(1).tolist()
    initial_guesses = {0:(1.2, 283000), 1:(1.2, 333000)} # ag_shutter combo
    main(camera_ids, search_range_again, search_range_shutter, output_dir, initial_guesses)
    
