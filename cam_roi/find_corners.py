import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import glob
class ChessboardCornerDetector:
    def __init__(self, pattern_size=(8, 5)):
        """
        Initialize the chessboard corner detector
        
        Args:
            pattern_size: tuple (columns, rows) of inner corners
            For 9 rows x 6 columns of squares, we have (6, 9) inner corners
        """
        self.pattern_size = pattern_size  # (6, 9) for 9 rows x 6 columns of squares
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        
        # Arrays to store object points and image points from all images
        self.obj_points = []  # 3D points in real world space
        self.img_points = []  # 2D points in image plane
        
        # Prepare object points (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
        self.objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:pattern_size[1], 0:pattern_size[0]].T.reshape(-1, 2)
        
        # Calibration matrices
        self.camera_matrix = None
        self.dist_coeffs = None
        self.rvecs = None
        self.tvecs = None
        
    def detect_corners_single_image(self, img_path, show_result=True):
        """
        Detect chessboard corners in a single image
        
        Args:
            img_path: path to the image file
            show_result: whether to display the result
            
        Returns:
            corners: detected corners if found, None otherwise
        """
        img = cv2.imread(img_path)
        
        if img is None:
            print(f"Error: Could not load image {img_path}")
            return None
        if 'cam0' in img_path:
            print('Green ch')
            gray = img[:,:,1]
        if 'cam1' in img_path:
            print('UV ch')
            gray = img[:,:,0]
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
        
        if ret:
            # Refine corner positions
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            
            if show_result:
                # Draw and display the corners
                img_with_corners = img.copy()
                cv2.drawChessboardCorners(img_with_corners, self.pattern_size, corners_refined, ret)
                
                plt.figure(figsize=(12, 8))
                plt.subplot(1, 2, 1)
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                plt.title('Original Image')
                plt.axis('off')
                
                plt.subplot(1, 2, 2)
                plt.imshow(cv2.cvtColor(img_with_corners, cv2.COLOR_BGR2RGB))
                plt.title('Detected Corners')
                plt.axis('off')
                
                plt.tight_layout()
                plt.show()
            
            return corners_refined
        else:
            print(f"Chessboard corners not found in {img_path}")
            return None
    
    def calibrate_camera(self, images_folder, file_pattern="*.jpg"):
        """
        Perform camera calibration using multiple chessboard images
        
        Args:
            images_folder: path to folder containing calibration images
            file_pattern: pattern for image files (e.g., "*.jpg", "*.png")
        """
        images_path = os.path.join(images_folder, file_pattern)
        images = glob.glob(images_path)
        
        if not images:
            print(f"No images found matching pattern: {images_path}")
            return False
        
        print(f"Found {len(images)} images for calibration")
        
        successful_calibrations = 0
        img_size = None
        
        for i, fname in enumerate(images):
            print(f"Processing image {i+1}/{len(images)}: {os.path.basename(fname)}")
            
            img = cv2.imread(fname)
            if img is None:
                continue
                
            if 'cam0' in fname:
                gray = img[:,:,1]   # cam0 img,Green
            if 'cam1' in fname:
                gray = img[:,:,0]   # cam1 img,UV
            
            if img_size is None:
                img_size = gray.shape[::-1]
            
            # Find chessboard corners
            ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
            
            if ret:
                successful_calibrations += 1
                
                # Refine corner positions
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                
                self.obj_points.append(self.objp)
                self.img_points.append(corners_refined)
                
                # Optional: Draw corners for this image
                img_with_corners = img.copy()
                cv2.drawChessboardCorners(img_with_corners, self.pattern_size, corners_refined, ret)
                
                # Save image with corners
                output_path = f"corners_detected_{os.path.basename(fname)}"
                cv2.imwrite(output_path, img_with_corners)
                print(f"Saved corners visualization: {output_path}")
            else:
                print(f"  - Chessboard not found in {os.path.basename(fname)}")
        
        if successful_calibrations < 3:
            print(f"Need at least 3 successful detections. Found only {successful_calibrations}")
            return False
        
        print(f"\nSuccessfully processed {successful_calibrations} images for calibration")
        
        # Perform camera calibration
        ret, self.camera_matrix, self.dist_coeffs, self.rvecs, self.tvecs = cv2.calibrateCamera(
            self.obj_points, self.img_points, img_size, None, None)
        
        if ret:
            print("Camera calibration successful!")
            self._print_calibration_results()
            return True
        else:
            print("Camera calibration failed!")
            return False
    
    def _print_calibration_results(self):
        """Print the calibration matrices and parameters"""
        print("\n" + "="*50)
        print("CALIBRATION RESULTS")
        print("="*50)
        
        print("\nCamera Matrix (Intrinsic Parameters):")
        print(self.camera_matrix)
        
        print("\nDistortion Coefficients:")
        print(self.dist_coeffs)
        
        # Calculate reprojection error
        mean_error = self._calculate_reprojection_error()
        print(f"\nMean Reprojection Error: {mean_error:.6f} pixels")
        
    def _calculate_reprojection_error(self):
        """Calculate mean reprojection error"""
        total_error = 0
        for i in range(len(self.obj_points)):
            img_points2, _ = cv2.projectPoints(self.obj_points[i], self.rvecs[i], self.tvecs[i], 
                                             self.camera_matrix, self.dist_coeffs)
            error = cv2.norm(self.img_points[i], img_points2, cv2.NORM_L2) / len(img_points2)
            total_error += error
        
        return total_error / len(self.obj_points)
    
    def save_calibration_data(self, filename="camera_calibration.npz"):
        """Save calibration data to file"""
        np.savez(filename,
                 camera_matrix=self.camera_matrix,
                 dist_coeffs=self.dist_coeffs,
                 rvecs=self.rvecs,
                 tvecs=self.tvecs)
        print(f"\nCalibration data saved to {filename}")
    
    def load_calibration_data(self, filename="camera_calibration.npz"):
        """Load calibration data from file"""
        try:
            data = np.load(filename)
            self.camera_matrix = data['camera_matrix']
            self.dist_coeffs = data['dist_coeffs']
            self.rvecs = data['rvecs']
            self.tvecs = data['tvecs']
            print(f"Calibration data loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"Calibration file {filename} not found")
            return False
    
    def undistort_image(self, img_path, output_path=None):
        """Undistort an image using the calibration parameters"""
        if self.camera_matrix is None or self.dist_coeffs is None:
            print("Camera not calibrated yet!")
            return None
        
        img = cv2.imread(img_path)
        if img is None:
            print(f"Error: Could not load image {img_path}")
            return None
        
        h, w = img.shape[:2]
        
        # Get optimal new camera matrix
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix, self.dist_coeffs, (w, h), 1, (w, h))
        
        # Undistort
        undistorted = cv2.undistort(img, self.camera_matrix, self.dist_coeffs, None, new_camera_matrix)
        
        # Crop the image
        x, y, w, h = roi
        undistorted = undistorted[y:y+h, x:x+w]
        
        if output_path:
            cv2.imwrite(output_path, undistorted)
            print(f"Undistorted image saved to {output_path}")
        
        # Display comparison
        plt.figure(figsize=(15, 6))
        plt.subplot(1, 2, 1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title('Original Image (Distorted)')
        plt.axis('off')
        
        plt.subplot(1, 2, 2)
        plt.imshow(cv2.cvtColor(undistorted, cv2.COLOR_BGR2RGB))
        plt.title('Undistorted Image')
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        
        return undistorted
crop_path = sys.argv[1]+'cropped/'
print('crop_path:', crop_path)
# to_find_corners = glob.glob(crop_path+'*.jpg')
def main(crop_path):
    """
    Main function demonstrating the complete workflow
    """
    # Initialize detector with 9 rows x 6 columns pattern (6,9 inner corners)
    detector = ChessboardCornerDetector(pattern_size=(8,5))
    
    # Option 1: Single image corner detection
    print("=== SINGLE IMAGE CORNER DETECTION ===")
    single_image_path = "chessboard_image.jpg"  # Replace with your image path
    if os.path.exists(single_image_path):
        corners = detector.detect_corners_single_image(single_image_path, show_result=True)
    
    # Option 2: Full camera calibration with multiple images
    print("\n=== FULL CAMERA CALIBRATION ===")
    images_folder = crop_path
    # os.makedirs(images_folder, exist_ok=True)
    
    if os.path.exists(images_folder):
        # Perform calibration
        success = detector.calibrate_camera(images_folder, "*.jpg")
        
        if success:
            # Save calibration data
            detector.save_calibration_data(images_folder+"my_camera_calibration.npz")
            
            # Demonstrate undistortion on a test image
            test_image = "test_image.jpg"  # Replace with your test image
            if os.path.exists(test_image):
                print("\n=== IMAGE UNDISTORTION DEMONSTRATION ===")
                detector.undistort_image(test_image, "undistorted_output.jpg")
    
    # Option 3: Load existing calibration data
    print("\n=== LOADING EXISTING CALIBRATION ===")
    if os.path.exists("camera_calibration.npz"):
        detector.load_calibration_data("camera_calibration.npz")
        
        # Use loaded calibration to undistort an image
        test_image = "test_image.jpg"
        if os.path.exists(test_image):
            detector.undistort_image(test_image, "undistorted_loaded.jpg")
if __name__ == "__main__":
    main(crop_path)
        
        