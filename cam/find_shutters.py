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

def call_bash_script(camera_id, shutter, analoggain):
    # Ensure the data directory exists
    os.makedirs(CAM_PATH, exist_ok=True)
    
    # Construct the output image filename
    img_filename = os.path.join(output_dir, f"cam{camera_id}_shutter{shutter}_ag{analoggain}.jpg")
    
    ## Call the bash script
    # bash takes:
    # $1 absolute path of the output image file as the first argument
    # $2 camera ID as the second argument
    # $3 shutter speed in microseconds as the third argument
    # $4 analog gain as the fourth argument
    subprocess.run(["bash", os.path.join(CAM_PATH,"cam_take_photo.sh"),img_filename,
                    str(camera_id), str(shutter), str(analoggain)], check=True)
    
    # Wait for the image file to be generated
    if not os.path.exists(img_filename):
        raise FileNotFoundError(f"Image file {img_filename} not found after calling the bash script.")
    
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

def main():
    # Define ranges for parameters
    analoggain = 1.2 # Analog gain from 1.2 to 8 with 0.4 spacing
    camera_ids = [0, 1]  # Camera IDs
    shutter_range = range(int(33*1e3), int(1033e3), int(50e3))  # Shutter speed from 33,000 to 1,033,000 in steps of 10,000

    # Initialize results dictionary
    results = []

    for camera_id in camera_ids:
        found_ok = False
        for analoggain in [ii/10.0 for ii in range(12,81,4)]:
            if found_ok:
                break
            for shutter in shutter_range:
                try:
                    img_filename = call_bash_script(camera_id, shutter, analoggain)
                    exposure_status = analyze_image(img_filename)
                    if exposure_status in ["overexposed", "underexposed"]:
                        os.remove(img_filename)
                        print(f"The image {img_filename} is {exposure_status}. Moving to the next combination.")
                        continue
                    else:
                        print(f"The image {img_filename} is {exposure_status}.")
                        results.append([camera_id,analoggain,shutter])
                        found_ok = True
                        break
                except Exception as e:
                    print(f"Error: {e}")
                    print(f"An error occurred for camera_id={camera_id}, shutter={shutter}, analoggain={analoggain}: {e}")
                    
    output_file = os.path.join(output_dir, 'cam_shutter_ag.npy')
    np.save(output_file,results)
    
    cam_config_file = os.path.join(DATA_PATH, "cam_shutter_ag.npy")
    np.save(cam_config_file,results)
if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(CAM_PATH, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    main()