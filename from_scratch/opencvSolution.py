import numpy as np
import cv2 as cv
import sys
import glob
import os
 
# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
 
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((5*8,3), np.float32)
objp[:,:2] = np.mgrid[0:8,0:5].T.reshape(-1,2)
 
# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.
 
img_folder = sys.argv[1]
cropped_folder = os.path.join(img_folder, "cropped")
vigged_folder = os.path.join(img_folder, "cropped_vig_corrected")
cornered_folder = os.path.join(img_folder, "cropped_corners")
os.makedirs(cropped_folder, exist_ok=True)
os.makedirs(vigged_folder, exist_ok=True)
os.makedirs(cornered_folder, exist_ok=True)

img_paths = glob.glob(os.path.join(vigged_folder, "*.jpg"))
 
for fname in img_paths:
    img = cv.imread(fname)
    if 'cam0' in fname:
        gray = img[:,:,1]
    if 'cam1' in fname:
        gray = img[:,:,0]
 
    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (8,5), None)
 
    # If found, add object points, image points (after refining them)
    if ret == True:
        print(f"Chessboard corners found in {fname}")
        objpoints.append(objp)
 
        corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners2)
 
        # # Draw and display the corners
        # cv.drawChessboardCorners(img, (7,6), corners2, ret)
        # cv.imshow('img', img)
        # cv.waitKey(500)
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
print("Camera matrix : \n")
print(mtx)
print("dist : \n")
print(dist)
print("rvecs : \n")
print(rvecs)
print("tvecs : \n")
print(tvecs)