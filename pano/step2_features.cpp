#include <opencv2/opencv.hpp>
#include <opencv2/stitching/detail/matchers.hpp>

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
    
    // HomographyBasedEstimator estimator;
    // std::vector<CameraParams> cameras;
    

    // if (!estimator(features, pairwise_matches, cameras)) {
    //     cout << "Homography estimation failed" << endl;
    //     return -1;
    // }

    // // sanity check
    // for (size_t i = 0; i < cameras.size(); ++i) {
    //     cout << "Camera " << i
    //          << " focal=" << cameras[i].focal
    //          << endl;
    // }
    // for (auto& cam : cameras)
    //     cam.R = cam.R.clone();  // REQUIRED
         
    // return 0;
}
