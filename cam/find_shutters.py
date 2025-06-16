import subprocess
import os
import numpy as np
import cv2


# Define paths globally
HOME = os.path.expanduser("~")
SCAM_PATH = os.path.join(HOME, "Github", "SCAM")
CAM_PATH = os.path.join(SCAM_PATH, 'cam')

def call_bash_script(camera_id, shutter, analoggain):
    # Ensure the data directory exists
    os.makedirs(CAM_PATH, exist_ok=True)
    
    # Construct the output image filename
    img_filename = os.path.join(CAM_PATH, f"cam{camera_id}_shutter{shutter}_ag{analoggain}.jpg")
    
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
        brightness = np.mean(img[:,:,1])  # Convert to grayscale and calculate mean brightness
    if 'cam1' in img_filename:
        brightness = np.mean(img[:,:,0])  # Convert to grayscale and calculate mean brightness
    
    # Define thresholds for overexposure and underexposure
    overexposed_threshold = 240  # Example threshold for overexposure
    underexposed_threshold = 15  # Example threshold for underexposure
    
    if brightness > overexposed_threshold:
        return "overexposed"
    elif brightness < underexposed_threshold:
        return "underexposed"
    else:
        return "properly exposed"

def main():
    # Example parameters
    camera_id = 0
    shutter = 1000  # in microseconds
    analoggain = 2.0  # gain value
    
    try:
        # Call the bash script and get the image filename
        img_filename = call_bash_script(camera_id, shutter, analoggain)
        
        # Analyze the image
        exposure_status = analyze_image(img_filename)
        print(f"The image {img_filename} is {exposure_status}.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()