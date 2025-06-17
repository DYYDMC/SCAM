import subprocess
import os
import numpy as np
import cv2
from datetime import datetime

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
        brightness = np.mean(img[100:-100,:-500,1])  # Convert to grayscale and calculate mean brightness
    if 'cam1' in img_filename:
        brightness = np.mean(img[100:-100,:-500,0])  # Convert to grayscale and calculate mean brightness
    
    # Define thresholds for overexposure and underexposure
    overexposed_threshold = 240  # Example threshold for overexposure
    underexposed_threshold = 50  # Example threshold for underexposure
    
    if brightness > overexposed_threshold:
        return "overexposed"
    elif brightness < underexposed_threshold:
        return "underexposed"
    else:
        return "ok"
def search_exposure(camera_ids, shutter_range, again_range, output_dir, initial_guesses=None):
    results = {}
    cam0_found = False
    cam1_found = False
    # try the initial guesses first
    if initial_guesses:
        for camera_id, analoggain, shutter in initial_guesses:
            try:
                print('TRYING INITIAL GUESS!!!!!!!!!!!!!!')
                img_filename = call_bash_script(camera_id, shutter, analoggain, output_dir)
                exposure_status = analyze_image(img_filename)
                
                if exposure_status == "ok":
                    results.append([camera_id, analoggain, shutter])
                    print(f"Found good settings: cam{camera_id}, shutter={shutter}, again={analoggain}")
                    results[int(camera_id)] =(shutter,analoggain)
                    if int(camera_id) == 0:
                        cam0_found = True
                    else:
                        cam1_found = True
                        
                else:
                    os.remove(img_filename)
    if cam0_found and cam1_found:
        return results
    elif cam0_found:
        ref_shutter,ref_analoggain = results[0]
        new_again_range = range(ref_analoggain,again_range.stop,again_range.step)
        new_shutter_range = range(ref_shutter,shutter_range.stop,shutter_range.step)
        for analoggain in new_again_range:
            for shutter in new_shutter_range:
                try:
                    print('TRYING!!!!!!!!!!!!!!')
                    img_filename = call_bash_script(camera_id, shutter, analoggain, output_dir)
                    print(img_filename)
                    exposure_status = analyze_image(img_filename)
                    
                    if exposure_status == "ok":
                        results[1] =(shutter,analoggain)
                        cam1_found = True
                        return results
                    else:
                        os.remove(img_filename)
    else:
        for camera_id in camera_ids:
            for analoggain in new_again_range:
                for shutter in new_shutter_range:
                    try:
                        print('TRYING!!!!!!!!!!!!!!')
                        img_filename = call_bash_script(camera_id, shutter, analoggain, output_dir)
                        print(img_filename)
                        exposure_status = analyze_image(img_filename)
                        
                        if exposure_status == "ok":
                            results[int(camera_id)] =(shutter,analoggain)
                            cam1_found = True
                            return results
                        else:
                            os.remove(img_filename)
    return results

def main(camera_ids, shutter_range, again_range, output_dir, initial_guesses=None):
    results = search_exposure(camera_ids, shutter_range, again_range, output_dir, initial_guesses)
    print(results,type(results))
    print(len(results))
    toSave = np.copy(results)
    print(toSave)
    np.save(os.path.join(output_dir, 'cam_shutter_ag.npy'), toSave)
    print(toSave)
    np.save(os.path.join(DATA_PATH, "cam_shutter_ag.npy"), toSave)
    print(toSave)
    return results
if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(CAM_PATH, timestamp)
    camera_ids = [0, 1]
    shutter_range = range(int(33e3), int(1033e3), int(50e3))
    again_range = [round(ii / 10.0, 1) for ii in range(12, 81, 4)]
    initial_guesses = [
    (0, 1.2, 633000),
    (1, 2.0, 833000)]
    main(camera_ids, shutter_range, again_range, output_dir, initial_guesses)
