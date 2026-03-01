%% UV-Green homography presentation demo
% Visualizes feature detection, matching, inliers, and final registration overlay.

scriptDir = fileparts(mfilename('fullpath'));
cam0Path = fullfile(scriptDir, 'square_masked_cam0.tiff'); % green
cam1Path = fullfile(scriptDir, 'square_masked_cam1.tiff'); % uv

if ~isfile(cam0Path) || ~isfile(cam1Path)
    error('square_masked_cam0.tiff or square_masked_cam1.tiff not found in %s', scriptDir);
end

img0 = imread(cam0Path);
img1 = imread(cam1Path);

img0Gray = im2gray(img0);
img1Gray = im2gray(img1);

%% 1) Input pair
figure('Name', 'Input Square Crops');
tiledlayout(1,2, 'Padding', 'compact', 'TileSpacing', 'compact');
nexttile; imshow(img0); title('cam0 (green) square crop');
nexttile; imshow(img1); title('cam1 (uv) square crop');
sgtitle('Input images for registration');

%% 2) Feature detection
points0 = detectSURFFeatures(img0Gray);
points1 = detectSURFFeatures(img1Gray);

figure('Name', 'Detected SURF Features');
tiledlayout(1,2, 'Padding', 'compact', 'TileSpacing', 'compact');
nexttile; imshow(img0Gray); hold on; plot(points0.selectStrongest(300)); title('cam0 (green) SURF features');
nexttile; imshow(img1Gray); hold on; plot(points1.selectStrongest(300)); title('cam1 (uv) SURF features');
sgtitle('Feature detection');

%% 3) Feature extraction + matching
[features0, validPoints0] = extractFeatures(img0Gray, points0);
[features1, validPoints1] = extractFeatures(img1Gray, points1);

indexPairs = matchFeatures(features0, features1, 'Unique', true);
matchedPoints0 = validPoints0(indexPairs(:,1));
matchedPoints1 = validPoints1(indexPairs(:,2));

figure('Name', 'Feature Matches (Raw)');
showMatchedFeatures(img0Gray, img1Gray, matchedPoints0, matchedPoints1, 'montage');
title(sprintf('Raw matches: %d pairs', size(indexPairs,1)));

%% 4) Homography estimation (projective) + inlier visualization
if size(indexPairs,1) < 4
    error('Not enough matched pairs for homography: %d found', size(indexPairs,1));
end

[tform0To1, inlierIdx] = estgeotform2d(matchedPoints0, matchedPoints1, ...
    'projective', Confidence=99.9, MaxNumTrials=3000);

inlierPoints0 = matchedPoints0(inlierIdx);
inlierPoints1 = matchedPoints1(inlierIdx);

figure('Name', 'Inlier Matches (Projective)');
showMatchedFeatures(img0Gray, img1Gray, inlierPoints0, inlierPoints1, 'montage');
title(sprintf('Inlier matches after RANSAC: %d / %d', numel(inlierIdx), size(indexPairs,1)));

%% 5) Warp + overlay result (cam1 fixed, cam0 warped)
outputRef = imref2d(size(img1Gray));
warped0 = imwarp(img0, tform0To1, OutputView=outputRef);

% RGB overlay: green channel from warped cam0, blue channel from cam1.
overlay = zeros([size(img1Gray,1), size(img1Gray,2), 3], 'like', img1);
overlay(:,:,2) = im2gray(warped0);
overlay(:,:,3) = img1Gray;

figure('Name', 'Registered Overlay');
imshow(overlay);
title('Registration end result: RGB overlay (G=warped cam0, B=cam1)');

%% Optional saves for slides
imwrite(overlay, fullfile(scriptDir, 'uv_green_registered_overlay.tiff'));
