import subprocess
import os
import sys
import numpy as np
import cv2
from datetime import datetime
import pickle

# Define paths globally
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM_PATH = os.path.join(SCAM_PATH, 'cam')
DATA_PATH = os.path.join(SCAM_PATH, 'data')

def call_bash_script(camera_id, shutter, analoggain, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    img_filename = os.path.join(output_dir, f"cam{camera_id}_shutter{shutter}_ag{analoggain}.jpg")
    subprocess.run(["bash", os.path.join(CAM_PATH,"cam_take_photo.sh"), img_filename,
                    str(camera_id), str(shutter), str(analoggain)], check=True)
    if not os.path.exists(img_filename):
        raise FileNotFoundError(f"{img_filename} not created.")
    return img_filename

def analyze_image(img_filename):
    # Open the image
    img = cv2.imread(img_filename)  # Read the image using OpenCV
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB format
    
    # Calculate the brightness of the image
    if 'cam0' in img_filename:
        brightness = np.mean(img[500:-500,:-1296,1])  # Convert to grayscale and calculate mean brightness
    if 'cam1' in img_filename:
        brightness = np.mean(img[500:-500,:-1296,0])  # Convert to grayscale and calculate mean brightness
    
    # Define thresholds for overexposure and underexposure
    overexposed_threshold = 240  # Example threshold for overexposure
    underexposed_threshold = 50  # Example threshold for underexposure
    
    if brightness > overexposed_threshold:
        return "overexposed"
    elif brightness < underexposed_threshold:
        return "underexposed"
    else:
        return "ok"
# Core search function
def adaptive_search_exposure(camera_id, output_dir, initial_tuple=(1.2,33000)):
    min_shutter, max_shutter, step_shutter = int(33e3), int(1033e3), int(50e3)
    min_again, max_again, step_again = 1.2, 8.1, 0.4
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
            dir_change = "increase" if result == "underexposed" else "decrease"
            new_range_again = update_range(search_range_again, current_ag, dir_change)
            new_range_shutter = update_range(search_range_shutter, current_shutter, dir_change)
            
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
    