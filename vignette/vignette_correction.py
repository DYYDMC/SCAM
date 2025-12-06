import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import os
Class VignetteCorrector:
    """
    Class to handle vignette correction for images.
    """
    def __init__(self):
        pass
    def generate_vignette_mask(self,image_paths, num_samples=4):
        # generate vignette template from images of uniformly illuminated white wall
        num_samples = 4
        vignette_mask = None
        for i in range(num_samples):
            img = cv2.imread(f"./cam1_cropped_Sunday_whitecam1_{i}.jpg")
            if vignette_mask is None:
                vignette_mask = img.astype(np.float32)
            else:
                vignette_mask += img.astype(np.float32)
        vignette_mask /= num_samples
        vignette_mask = vignette_mask / np.max(vignette_mask)
        
    def correct_vignette(img, vignette_mask):
        """
        img:path to target image
        vignette_mask: numpy array of vignette mask
        Correct the vignette effect in the image using the provided vignette mask.
        """
        imgfloat32 = cv2.imread(img).astype(np.float32)
        
        # Debug: Print shapes
        print(f"Image shape: {imgfloat32.shape}")
        print(f"Mask shape: {vignette_mask.shape}")
        
        # Check if shapes match
        if imgfloat32.shape != vignette_mask.shape:
            print("Shapes don't match! Resizing mask to match image...")
            vignette_mask = cv2.resize(vignette_mask, (imgfloat32.shape[1], imgfloat32.shape[0]))
        
        corrected_img = cv2.divide(imgfloat32, vignette_mask)
        corrected_img_clipped = np.clip(corrected_img, 0, 255).astype(np.uint8)
        
        return corrected_img_clipped
    def load_vignette_mask(mask_path):
        """
        Load vignette mask from a .npy file.
        
        Args:
            mask_path (str): Path to the .npy file containing the vignette mask.
        """
        vignette_mask = np.load(mask_path)
        return vignette_mask
    def correct_vignette(self,img,vignette_mask):
        """
        img:path to target image
        vignette_mask: numpy array of vignette mask
        Correct the vignette effect in the image using the provided vignette mask.
        """
        imgfloat32 = cv2.imread(img).astype(np.float32)
        corrected_img = cv2.divide(imgfloat32, vignette_mask)
        corrected_img_clipped = np.clip(corrected_img, 0, 255).astype(np.uint8)
        
        return corrected_img_clipped
# Example usage:
# first crop

# the ngenerate vignette mask

# generate vignette template from images of uniformly illuminated white wall
num_samples = 4
vignette_mask = None
for i in range(num_samples):
    img = cv2.imread(f"./cam1_cropped_Sunday_whitecam1_{i}.jpg")
    if vignette_mask is None:
        vignette_mask = img.astype(np.float32)
    else:
        vignette_mask += img.astype(np.float32)
vignette_mask /= num_samples

# 归一化模板（防止除以0）
vignette_mask = vignette_mask / np.max(vignette_mask)
cv2.imwrite("./cam1_vignette_mask.png", vignette_mask * 255)
np.save("./cam1_vignette_mask.npy", vignette_mask)