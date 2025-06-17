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
    found = {cam_id: False for cam_id in camera_ids}

    if initial_guesses:
        for camera_id, analoggain, shutter in initial_guesses:
            try:
                print(f"Trying initial guess: cam{camera_id}, shutter={shutter}, again={analoggain}")
                img_filename = call_bash_script(camera_id, shutter, analoggain, output_dir)
                if analyze_image(img_filename) == "ok":
                    results[camera_id] = (shutter, analoggain)
                    found[camera_id] = True
                    os.remove(img_filename)
                else:
                    os.remove(img_filename)
            except Exception as e:
                print(f"Initial guess failed: cam{camera_id}, shutter={shutter}, again={analoggain} -> {e}")

    if all(found.values()):
        return results

    for camera_id in camera_ids:
        if found[camera_id]:
            continue

        ref_shutter, ref_again = results.get(0, (shutter_range[0], again_range[0]))

        # Narrow search if cam0 was found
        agains = [x for x in again_range if x >= ref_again] if found.get(0) else again_range
        shutters = [x for x in shutter_range if x >= ref_shutter] if found.get(0) else shutter_range

        for analoggain in agains:
            for shutter in shutters:
                try:
                    print(f"Searching: cam{camera_id}, shutter={shutter}, again={analoggain}")
                    img_filename = call_bash_script(camera_id, shutter, analoggain, output_dir)
                    if analyze_image(img_filename) == "ok":
                        results[camera_id] = (shutter, analoggain)
                        found[camera_id] = True
                        os.remove(img_filename)
                        break
                    else:
                        os.remove(img_filename)
                except Exception as e:
                    print(f"Search failed: cam{camera_id}, shutter={shutter}, again={analoggain} -> {e}")
            if found[camera_id]:
                break

    return results


def main(camera_ids, shutter_range, again_range, output_dir, initial_guesses=None):
    os.makedirs(output_dir, exist_ok=True)

    results = search_exposure(camera_ids, shutter_range, again_range, output_dir, initial_guesses)
    print(f"Final results: {results}")

    # Convert dict to sorted array for consistent storage
    to_save = np.array([[cam_id, ag, sh] for cam_id, (sh, ag) in sorted(results.items())])
    np.save(os.path.join(output_dir, 'cam_shutter_ag.npy'), to_save)
    np.save(os.path.join(DATA_PATH, 'cam_shutter_ag.npy'), to_save)

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
