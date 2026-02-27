%% load preprocessed images
img_l_full = imread('tilt_10_left.tiff'); % left
img_r_full = imread('tilt_10_right.tiff'); % right
%%
% crop or select ROIs (from visual inspection)
img_l = img_l_full;% crop_pano_to_largest_valid_rect(img_l_full);
img_r = img_r_full;%crop_pano_to_largest_valid_rect(img_r_full);

% keep RGB for final panorama
img_l_rgb = img_l;
img_r_rgb = img_r;

% create grayscale copies for feature detection
img_l_gray = im2gray(img_l_rgb);
img_r_gray = im2gray(img_r_rgb);

% detect and extract SURF features
points_left = detectSURFFeatures(img_l_gray);
[features_left, points_left] = extractFeatures(img_l_gray, points_left);

points_right = detectSURFFeatures(img_r_gray);
[features_right, points_right] = extractFeatures(img_r_gray, points_right);

% match features
indexPairs = matchFeatures(features_left, features_right, 'Unique', true);

matchedPointsLeft = points_left(indexPairs(:,1));
matchedPointsRight = points_right(indexPairs(:,2));

% estimate geometric transform (projective)
tformRightToLeft = estimateGeometricTransform2D(matchedPointsRight, matchedPointsLeft, ...
    'projective', 'Confidence', 99.9, 'MaxNumTrials', 2000);

% compute output limits to determine panorama size
imageSizeLeft = size(img_l_rgb);
imageSizeRight = size(img_r_rgb);

[xLimitsLeft, yLimitsLeft] = outputLimits(projective2d(eye(3)), [1 imageSizeLeft(2)], [1 imageSizeLeft(1)]);
[xLimitsRight, yLimitsRight] = outputLimits(tformRightToLeft, [1 imageSizeRight(2)], [1 imageSizeRight(1)]);

xMin = min([xLimitsLeft xLimitsRight]);
xMax = max([xLimitsLeft xLimitsRight]);
yMin = min([yLimitsLeft yLimitsRight]);
yMax = max([yLimitsLeft yLimitsRight]);

width  = round(xMax - xMin);
height = round(yMax - yMin);

xWorldLimits = [xMin xMax];
yWorldLimits = [yMin yMax];

% create a 2-D spatial reference object defining the size of the panorama
outputView = imref2d([height width], xWorldLimits, yWorldLimits);

% warp images into the panorama
warpedLeft  = imwarp(img_l_rgb,  projective2d(eye(3)), 'OutputView', outputView);
warpedRight = imwarp(img_r_rgb, tformRightToLeft, 'OutputView', outputView);

% create a simple blending mask for each warped image
maskLeft  = imwarp(true(size(img_l_rgb,1), size(img_l_rgb,2)), projective2d(eye(3)), 'OutputView', outputView);
maskRight = imwarp(true(size(img_r_rgb,1), size(img_r_rgb,2)), tformRightToLeft, 'OutputView', outputView);

% Convert masks to double for blending weights
maskLeft  = double(maskLeft);
maskRight = double(maskRight);

% Avoid division by zero: compute combined mask
maskSum = maskLeft + maskRight;
maskSum(maskSum == 0) = 1;

%%
panorama = zeros([height width 3],"like",img_l_rgb);

panorama = imblend(warpedLeft,panorama,maskLeft,foregroundopacity=1);
panorama = imblend(warpedRight,panorama,maskRight,foregroundopacity=1);

imshow(panorama)
%% rotate so that the horizon is actually horizontal
% Simple rotate (default is 'loose' so nothing is cut off)
panorama_rotat= imrotate(panorama, 2, 'bilinear');
imshowpair(panorama,panorama_rotat)
%%
% display panorama
figure; imshow(panorama); title('Stitched Panorama');

%% optionally save result
imwrite(panorama, 'panorama_uncroppedLR_stitched_tilt10.tiff');
imwrite(panorama_rotat, 'panorama_uncroppedLR_stitched_tilt10_rotated.tiff');