import cv2
import numpy as np

def align_images(img_path1, img_path2, output_path='aligned4.jpg', flip_img2=False):
    # Load images
    img1 = cv2.imread(img_path1, cv2.IMREAD_COLOR)
    img2 = cv2.imread(img_path2, cv2.IMREAD_COLOR)

    if img1 is None or img2 is None:
        raise FileNotFoundError("One or both image paths are invalid.")

    # Optionally flip img2 vertically (Y-axis)
    if flip_img2:
        img2 = cv2.flip(img2, 0)

    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Detect and compute keypoints/descriptors using ORB
    orb = cv2.ORB_create(nfeatures=5000)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    # Match descriptors
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    # Sort by distance
    matches = sorted(matches, key=lambda x: x.distance)

    # Extract matched keypoints
    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches[:50]]).reshape(-1, 1, 2)

    # Compute homography
    H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

    # Warp img2 to img1's frame
    height, width = img1.shape[:2]
    aligned_img2 = cv2.warpPerspective(img2, H, (width, height))

    # Save and return the aligned image
    cv2.imwrite(output_path, aligned_img2)
    return aligned_img2

# Example usage:
aligned = align_images('./cam0/morning_DZNE/cropped/cam0_cropped_cam0_4.jpg', './cam1/morning_DZNE/cropped/cam1_cropped_cam1_4_undistorted.jpg', flip_img2=True)
