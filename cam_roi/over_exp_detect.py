import cv2
import numpy as np
import os
import sys

# Ensure proper usage
if len(sys.argv) < 3:
    print("Usage: python over_exp_detect.py <video_path> <camera_id>")
    sys.exit(1)

video_path = sys.argv[1]
# print(f':??????does the {video_path} exist?', os.path.exists(video_path))
camera_id = int(sys.argv[2])  # Convert input to integer
# Validate camera_id
if camera_id not in [0, 1, 2]:
    print("Invalid camera_id. Use 0 for Blue, 1 for Green, 2 for Red.")
    sys.exit(1)

OVEREXP_THRESHOLD = 0.0005 # before 2. April 2025 0.00028 
UNDEREXP_INT_THRESHOLD = 100 # before 2.April 2025 50 # randomly decided
cap = cv2.VideoCapture(video_path)
#print(type(cap))
#print('0????????????????????are you here at all?????????????????????')
def get_overExp(snippet):
    numF,H,W = snippet.shape
    perc_overExp = np.zeros(numF)
    for ff in range(numF):
        frame = snippet[ff]
        num_255_pixels = np.sum(frame == 255)
        percent_255_pixels = (num_255_pixels / (H*W))
        if percent_255_pixels>1:
            print('BUG')
            break
        perc_overExp[ff] = percent_255_pixels
    return perc_overExp
# print('1????????????????????are you here at all?????????????????????')
def get_underExp(snippet):
    # the percentage of frames whose mean intensity is less than UNDEREXP_INT_THRESHOLD
    numF,H,W = snippet.shape
    bool_underExp = [np.mean(snippet[ii]) < UNDEREXP_INT_THRESHOLD for ii in range(numF)]
    return bool_underExp
#print('3????????????????????are you here at all?????????????????????')
# Check if the video was opened successfully
# print(f"IS THERE {video_path} AT ALL", os.path.exists(video_path))

if not cap.isOpened():
    raise ValueError(f"Could not open video file: {video_path}")
#print('4????????????????????are you here at all?????????????????????')
# Initialize an empty list to store selected channels
cChannal = []
while True:
    ret, frame = cap.read()
    if not ret:
        break  # Exit the loop if no more frames are available

    # Extract the selected channel based on camera_id
    cChannal.append(frame[:, :, 1-camera_id]) # camera 0:green, camera 1: UV, color channal (0)blue->(1)green->red

# Release the video capture object
cap.release()
#print('5 ????????????????????are you here at all?????????????????????')
# Stack the selected channels into a 3D NumPy array
stacked = np.stack(cChannal, axis=0)
# print(stacked.shape) # shape (5, 324, 576) for EXP_adjustment
# np.save(f'./cam{camera_id}_stacked.npy', stacked)

perc_overExp = get_overExp(stacked)
bool_underExp = get_underExp(stacked)
#print(perc_overExp)
#print(bool_underExp)
ifUnder = True
ifOver= True

if np.sum(bool_underExp)/len(stacked) > 0.05:
    print('UNDEREXPOSED')
else:
    ifUnder = False

if np.min(perc_overExp)>OVEREXP_THRESHOLD:
    print('OVEREXPOSED')
else:
    ifOver = False
# print(ifUnder, ifOver)
if not ifUnder and not ifOver:
    print('OK')
