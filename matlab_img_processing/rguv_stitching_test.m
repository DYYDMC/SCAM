%% load preprocessed images
img0_full = imread('out1_rgb.tiff'); img0 = img0_full(100:end,50:end,:);
img1_full = imread('out2_rgb.tiff'); img1 = img1_full(100:end,50:end,:);
% Note: keep images as RGB (uint8 or uint16) to preserve color information.
% Do NOT convert to grayscale here if you want to retain color in the panorama.

% If you still need grayscale for feature detection, create grayscale copies
img1_gray = im2gray(img1);
img0_gray = im2gray(img0);

%% manually select paired features (returned its coordinates)
[mp,fp] = cpselect(img1_gray,img0_gray,Wait=true);

%% turn movingPoints and fixpoints' into SURF object
manualMovingPts1 = SURFPoints(mp);
manualFixPts0 = SURFPoints(fp);

%% feature extraction (use grayscale images for feature detection/extraction)
[features1, validPts1] = extractFeatures(img1_gray, manualMovingPts1);
[features0, validPts0] = extractFeatures(img0_gray, manualFixPts0);

%% feature matching
indexPairs = matchFeatures(features0, features1, 'Unique', true);
matched0 = validPts0(indexPairs(:,1));
matched1 = validPts1(indexPairs(:,2));

%% calculate the transformation matrix for fixedImg(img0) and movingImg(img1)
[movingT,inlierIdx,status] = estgeotform2d(manualMovingPts1, manualFixPts0, "similarity", Confidence=99);
fixedT = rigidtform2d(); % identity transform

%% initialize the Panorama
[nrows, ncols, ~] = size(img1);

[xlimFixed, ylimFixed] = outputLimits(fixedT,[1 ncols],[1 nrows]);
[xlimMoving, ylimMoving] = outputLimits(movingT,[1 ncols],[1 nrows]);

xMin = round(min([xlimMoving, xlimFixed]));
xMax = round(max([xlimMoving, xlimFixed]));
yMin = round(min([ylimMoving, ylimFixed]));
yMax = round(max([ylimMoving, ylimFixed]));

%% create the Panorama canvas (preserve class and 3 color channels)
width = xMax - xMin;
height = yMax - yMin;
panorama = zeros([height width 3], "like", img0); % RGB canvas with same data type

xLimits = [xMin xMax];
yLimits = [yMin yMax];
panoramaView = imref2d([height width], xLimits, yLimits);

% Warp the full-color RGB images into the panorama view
warpedImg1 = imwarp(img1, movingT, "OutputView", panoramaView);
warpedImg0 = imwarp(img0, fixedT, "OutputView", panoramaView);

% Create masks for blending (single-channel logical masks)
mask1 = imwarp(true(size(img1,1),size(img1,2)), movingT, OutputView=panoramaView);
mask0 = imwarp(true(size(img0,1),size(img0,2)), fixedT, OutputView=panoramaView);

% Blend RGB images into the panorama. imblend supports RGB inputs when panorama is RGB.
panorama = imblend(warpedImg0, panorama, mask0, foregroundopacity=1);
panorama = imblend(warpedImg1, panorama, mask1, foregroundopacity=1);

%% save intermediate panorama
dir = uigetdir("Title","Please select the folder to save the intermediate result.");

imwrite(panorama, fullfile(dir, sprintf(['panoramaVertical_uv.tiff'])));