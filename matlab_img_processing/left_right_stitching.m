%% Select one PANO folder and stitch all left/right panorama pairs per tilt
panoDir = uigetdir("Title", "Select a PANO_* folder");
if isequal(panoDir, 0)
    error("No folder selected.");
end

panoramaRoot = fullfile(panoDir, "panoramas");
if ~isfolder(panoramaRoot)
    error("panoramas folder not found under: %s", panoDir);
end

tiltDirs = dir(fullfile(panoramaRoot, "tilt_*"));
tiltDirs = tiltDirs([tiltDirs.isdir]);

for t = 1:numel(tiltDirs)
    tiltName = tiltDirs(t).name;
    tiltPath = fullfile(panoramaRoot, tiltName);

    leftDir = fullfile(tiltPath, "left");
    rightDir = fullfile(tiltPath, "right");
    if ~isfolder(leftDir) || ~isfolder(rightDir)
        fprintf("Skipping %s: missing left/ or right/ folder.\n", tiltName);
        continue;
    end

    leftFiles = dir(fullfile(leftDir, "*.tif*"));
    rightFiles = dir(fullfile(rightDir, "*.tif*"));
    if isempty(leftFiles) || isempty(rightFiles)
        fprintf("Skipping %s: missing left/right TIFF file.\n", tiltName);
        continue;
    end

    % There should be one file each; if multiple, pick the first alphabetically.
    [~, idxL] = sort({leftFiles.name});
    [~, idxR] = sort({rightFiles.name});
    leftPath = fullfile(leftFiles(idxL(1)).folder, leftFiles(idxL(1)).name);
    rightPath = fullfile(rightFiles(idxR(1)).folder, rightFiles(idxR(1)).name);

    outPath = fullfile(tiltPath, sprintf("%s_full_pano.tiff", tiltName));
    fprintf("Stitching %s\n  left:  %s\n  right: %s\n", tiltName, leftPath, rightPath);
    panorama = stitch_lr_pair(leftPath, rightPath);
    imwrite(panorama, outPath);
    fprintf("Saved: %s\n", outPath);
end

%% Local function: stitch one left/right pair
function panorama = stitch_lr_pair(leftPath, rightPath)
img_l_full = imread(leftPath);
img_r_full = imread(rightPath);

img_l_rgb = crop_pano_to_largest_valid_rect(img_l_full);
img_r_rgb = crop_pano_to_largest_valid_rect(img_r_full);

img_l_gray = im2gray(img_l_rgb);
img_r_gray = im2gray(img_r_rgb);

points_left = detectSURFFeatures(img_l_gray);
[features_left, points_left] = extractFeatures(img_l_gray, points_left);

points_right = detectSURFFeatures(img_r_gray);
[features_right, points_right] = extractFeatures(img_r_gray, points_right);

indexPairs = matchFeatures(features_left, features_right, 'Unique', true);
matchedPointsLeft = points_left(indexPairs(:,1));
matchedPointsRight = points_right(indexPairs(:,2));

tformRightToLeft = estimateGeometricTransform2D(matchedPointsRight, matchedPointsLeft, ...
    'projective', 'Confidence', 99.9, 'MaxNumTrials', 2000);

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
outputView = imref2d([height width], [xMin xMax], [yMin yMax]);

warpedLeft  = imwarp(img_l_rgb,  projective2d(eye(3)), 'OutputView', outputView);
warpedRight = imwarp(img_r_rgb, tformRightToLeft, 'OutputView', outputView);

maskLeft  = imwarp(true(size(img_l_rgb,1), size(img_l_rgb,2)), projective2d(eye(3)), 'OutputView', outputView);
maskRight = imwarp(true(size(img_r_rgb,1), size(img_r_rgb,2)), tformRightToLeft, 'OutputView', outputView);

panorama = zeros([height width 3], "like", img_l_rgb);
panorama = imblend(warpedLeft, panorama, double(maskLeft), foregroundopacity=1);
panorama = imblend(warpedRight, panorama, double(maskRight), foregroundopacity=1);
end
