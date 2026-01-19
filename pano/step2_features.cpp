#include <opencv2/opencv.hpp>
#include <opencv2/stitching/detail/matchers.hpp>
#include <opencv2/stitching/detail/warpers.hpp>
// where : /usr/include/opencv4/opencv2/stitching/detail/warpers.hpp

#include <iostream>
#include <vector>
#include <string>

using namespace cv;
using namespace cv::detail;
using std::cout;
using std::endl;
using std::vector;

int main(int argc, char** argv)
{
    vector<Mat> images;
images.reserve(argc - 1);

    if (argc < 3) {
        cout << "Usage: ./step2_features img1 img2 [img3 ...]" << endl;
        return -1;
    }

    // Create SIFT detector
    //Ptr<SIFT> sift = SIFT::create();
    Ptr<SIFT> sift = SIFT::create(
        0,        // nfeatures (0 = unlimited)
        3,        // nOctaveLayers
        0.01,     // contrastThreshold (DEFAULT 0.04 → LOWER THIS)
        10,       // edgeThreshold
        1.6       // sigma
    );

    // Prepare feature container
    vector<ImageFeatures> features(argc - 1);

    cout << "Loaded " << argc - 1 << " images." << endl;

    for (int i = 1; i < argc; ++i) {

        // Load 16-bit TIFF
        Mat img16 = imread(argv[i], IMREAD_UNCHANGED);
        if (img16.empty()) {
            cout << "Failed to load image: " << argv[i] << endl;
            return -1;
        }
        // Store original image for later use
        images.push_back(img16);

        // Convert to grayscale (still 16-bit)
        Mat gray16;
        if (img16.channels() == 3)
            cvtColor(img16, gray16, COLOR_BGR2GRAY);
        else
            gray16 = img16;

        // Convert to 8-bit for SIFT
        Mat gray8;
        gray16.convertTo(gray8, CV_8U, 1.0 / 256.0);

        // Debug check (keep until stable)
        cout << "Image " << (i - 1)
             << " depth=" << gray8.depth()
             << " channels=" << gray8.channels()
             << endl;

        // SIFT feature extraction
        sift->detectAndCompute(
            gray8,
            noArray(),
            features[i - 1].keypoints,
            features[i - 1].descriptors
        );

        features[i - 1].img_idx = i - 1;
        features[i - 1].img_size = gray8.size();

        if (features[i - 1].descriptors.empty()) {
            cout << "ERROR: No descriptors found." << endl;
            return -1;
        }
        
        
        cout << "Image " << (i - 1)
            << ": keypoints = "
            << features[i - 1].keypoints.size()
            << endl;
    }

    cout << "Feature extraction finished successfully." << endl;

    BestOf2NearestMatcher matcher(
        false,   // try_use_gpu
        0.3f     // match confidence
    );
    
    std::vector<MatchesInfo> pairwise_matches;
    
    // // OpenCV 4.6 syntax
    matcher(features, pairwise_matches);
    // // sanity check
    // for (size_t i = 0; i < pairwise_matches.size(); ++i) {
    //     cout << "Pair " << i
    //          << "  src=" << pairwise_matches[i].src_img_idx
    //          << "  dst=" << pairwise_matches[i].dst_img_idx
    //          << "  inliers=" << pairwise_matches[i].num_inliers
    //          << endl;
    // }    
    
    matcher.collectGarbage();
    
    cout << "Pairwise matches computed: "
         << pairwise_matches.size()
         << endl;
    
    // camera estimation
    HomographyBasedEstimator estimator;
    std::vector<CameraParams> cameras;
    
    if (!estimator(features, pairwise_matches, cameras)) {
        cout << "Homography estimation failed" << endl;
        return -1;
    }

    // sanity check
    for (size_t i = 0; i < cameras.size(); ++i) {
        cout << "Camera " << i
             << " focal=" << cameras[i].focal
             << endl;
    }
    // for (auto& cam : cameras)
    //     cam.R = cam.R.clone();  // REQUIRED

    // transfore homographyBasedEstimator from double to float
    for (auto& cam : cameras) {
        cam.R.convertTo(cam.R, CV_32F);
    }
    cout << "Camera estimation finished successfully." << endl;
    
    // bundle adjustment
    BundleAdjusterReproj adjuster;
    adjuster.setConfThresh(1.0);

    Mat refine_mask = Mat::zeros(3, 3, CV_8U);
    refine_mask.at<uchar>(0,0) = 1;
    refine_mask.at<uchar>(0,1) = 1;
    refine_mask.at<uchar>(0,2) = 1;
    refine_mask.at<uchar>(1,1) = 1;

    adjuster.setRefinementMask(refine_mask);

    if (!adjuster(features, pairwise_matches, cameras)) {
        cout << "Bundle adjustment failed" << endl;
        return -1;
    }

    // sanity check on the focal length after bundle adjustment
    for (size_t i = 0; i < cameras.size(); ++i) {
        cout << "Camera " << i
             << " focal=" << cameras[i].focal
             << endl;
    }
    cout << "bundle adjustment finished successfully." << endl;

    // warping
    Ptr<cv::detail::RotationWarper> warper(
        new cv::detail::CylindricalWarper(
            static_cast<float>(cameras[0].focal)
        )
    );

    // ==============================
    // STEP 8.1 — create masks
    // ==============================
    vector<Mat> masks(images.size());
        for (size_t i = 0; i < images.size(); ++i) {
            masks[i] = Mat(images[i].size(), CV_8U, Scalar::all(255));
        }

    // ==============================
    // STEP 8.2 — prepare containers
    // ==============================
    vector<Mat> images_warped(images.size());
    vector<Mat> masks_warped(images.size());
    vector<Point> corners(images.size());
    vector<Size> sizes(images.size());

    // ==============================
    // STEP 8.3 — warp loop
    // ==============================
    for (size_t i = 0; i < images.size(); ++i) {

        Mat K = cameras[i].K().clone();
        K.convertTo(K, CV_32F);

        corners[i] = warper->warp(
            images[i], K, cameras[i].R,
            INTER_LINEAR, BORDER_REFLECT,
            images_warped[i]
        );

        warper->warp(
            masks[i], K, cameras[i].R,
            INTER_NEAREST, BORDER_CONSTANT,
            masks_warped[i]
        );

        sizes[i] = images_warped[i].size();

        cout << "Warped image " << i
            << " size=" << sizes[i]
            << " corner=" << corners[i]
            << endl;
    }


    return 0;
}
