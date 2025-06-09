# code to extract 2 4-element tuples for roi area
import numpy as np
import cv2
import os

def get_roi(img_path,colorCh):
    """
    Calculate the region of interest (ROI) for a given image.

    Args:
        img_path (str): The file path to the image.
        colorCh (int): the color channel (cv2.imread mapping) 0 blue, 1 green, 2 red

    Returns:
        tuple: A tuple (x_start, y_start, x_end, y_end) representing the ROI.
               - x_start (float): The normalized starting x-coordinate of the ROI.
               - y_start (float): The normalized starting y-coordinate of the ROI (always 0).
               - x_delta (float): The normalized ending x-coordinate of the ROI.
               - x_delta (float): The normalized ending y-coordinate of the ROI (always 1).

    Note:
        The function reads the image from the given path, converts it to a numpy array,
        and calculates the ROI based on the maximum pixel values in the first color channel.
    """
    image_array = cv2.imread(img_path) # reads images in BGR order by default
    nrows,ncols,ncolor = image_array.shape
    start_cc = np.argmax(np.max(image_array[:,:,colorCh], axis=0) > 50)
    tmp_roi_xStart = start_cc/ncols

    # Return a tuple (x_start, y_start, x_end, y_end) representing the ROI
    return (tmp_roi_xStart,0,0.5,1)   

script_dir = os.path.dirname(__file__)
cam0_path = os.path.join(script_dir, 'roi_cam0.jpg')
cam1_path = os.path.join(script_dir, 'roi_cam1.jpg')

cam0_roi = np.array(get_roi(cam0_path,1)) # cv2.imread ch1 = green
cam1_roi = np.array(get_roi(cam1_path,0)) # cv2.imread ch0 = blue

np.save(os.path.join(script_dir, 'roi_cam0.npy'), cam0_roi)
np.save(os.path.join(script_dir, 'roi_cam1.npy'), cam1_roi)

print(f'Green cam roi {cam0_roi}')
print(f'UV cam roi {cam1_roi}')