%% Stitch 3 RGB TIFF images into one vertical panorama (top -> bottom)
% This script is adapted from RGUV_auto_stitching.mlx, but configured for
% vertical stacking of exactly 3 photos.
%
% Expected filenames: RGB_<number>.tif/.tiff (e.g., RGB_1.tiff, RGB_11.tiff, RGB_21.tiff)
% Sorting rule: numeric ascending by default (top -> bottom).

imageDir = uigetdir("Title", "Select folder containing 3 RGB TIFF images");
if isequal(imageDir, 0)
    error("No folder selected.");
end

panorama = stitch_vertical_three(imageDir);

[~, folderName] = fileparts(imageDir);
outPath = fullfile(imageDir, sprintf("%s_vertical3_green_panorama.tiff", folderName));
imwrite(panorama, outPath);
fprintf("Saved: %s\n", outPath);

%% Local function
function panorama = stitch_vertical_three(imageDir)
ds = imageDatastore(imageDir, "IncludeSubfolders", false);
files = ds.Files;

% Keep files named like prepro_adapthisteq_uv_<number>.tif/.tiff (1..3 digits)
isRgbTiff = ~cellfun('isempty', regexp(files, 'prepro_adapthisteq_green_[0-9]{1,3}\.tiff?$', 'once'));
files = files(isRgbTiff);
tokens = regexp(files, 'prepro_adapthisteq_green_([0-9]{1,3})\.tiff?$', 'tokens', 'once');

nums = nan(size(tokens));
for k = 1:numel(tokens)
    if ~isempty(tokens{k})
        nums(k) = str2double(tokens{k}{1});
    end
end

[~, order] = sort(nums, "descend", "MissingPlacement", "last");
files = files(order);

if numel(files) ~= 3
    error("Expected exactly 3 RGB TIFF files in %s, found %d.", imageDir, numel(files));
end

ds.Files = files;
numImages = numel(ds.Files);

I = crop_pano_to_largest_valid_rect(imread(ds.Files{1}));
grayImage = im2gray(I);

points = detectSURFFeatures(grayImage);
[features, points] = extractFeatures(grayImage, points);

tforms(numImages) = projtform2d;
imageSize = zeros(numImages, 2);
imageSize(1, :) = [size(I,1) size(I,2)];

for n = 2:numImages
    pointsPrevious = points;
    featuresPrevious = features;

    I_full = readimage(ds, n);
    I = crop_pano_to_largest_valid_rect(I_full);
    grayImage = im2gray(I);
    imageSize(n, :) = [size(I,1) size(I,2)];

    points = detectSURFFeatures(grayImage);
    [features, points] = extractFeatures(grayImage, points);

    indexPairs = matchFeatures(features, featuresPrevious, Unique=true);
    matchedPoints = points(indexPairs(:, 1), :);
    matchedPointsPrev = pointsPrevious(indexPairs(:, 2), :);

    modelOrder = ["projective", "affine", "similarity", "rigid"];
    minPairs = [4, 3, 2, 2];
    stepTform = [];

    for m = 1:numel(modelOrder)
        if size(indexPairs, 1) < minPairs(m)
            continue;
        end
        try
            stepTform = estgeotform2d(matchedPoints, matchedPointsPrev, ...
                modelOrder(m), Confidence=99.9, MaxNumTrials=2000);
            break;
        catch
        end
    end

    if isempty(stepTform)
        error("Failed to estimate transform between images %d and %d.", n-1, n);
    end

    tforms(n) = stepTform;
    tforms(n).A = tforms(n-1).A * tforms(n).A;
end

xlim = zeros(numImages, 2);
ylim = zeros(numImages, 2);
for idx = 1:numImages
    h = imageSize(idx, 1);
    w = imageSize(idx, 2);
    [xlim(idx, :), ylim(idx, :)] = outputLimits(tforms(idx), [1 w], [1 h]);
end

% Vertical-centric normalization: pick center image by Y location
avgYLim = mean(ylim, 2);
[~, idxSort] = sort(avgYLim);
centerIdx = floor((numImages + 1) / 2);
centerImageIdx = idxSort(centerIdx);

Tinv = invert(tforms(centerImageIdx));
for idx = 1:numImages
    tforms(idx).A = Tinv.A * tforms(idx).A;
end

for idx = 1:numImages
    h = imageSize(idx, 1);
    w = imageSize(idx, 2);
    [xlim(idx, :), ylim(idx, :)] = outputLimits(tforms(idx), [1 w], [1 h]);
end

maxImageSize = max(imageSize, [], 1);
xMin = min([1; xlim(:)]);
xMax = max([maxImageSize(2); xlim(:)]);
yMin = min([1; ylim(:)]);
yMax = max([maxImageSize(1); ylim(:)]);
width = round(xMax - xMin);
height = round(yMax - yMin);

panoramaView = imref2d([height width], [xMin xMax], [yMin yMax]);

I_first = crop_pano_to_largest_valid_rect(imread(ds.Files{1}));
if ndims(I_first) == 2
    panorama = zeros([height width], "like", I_first);
else
    panorama = zeros([height width size(I_first, 3)], "like", I_first);
end

for idx = 1:numImages
    I = crop_pano_to_largest_valid_rect(imread(ds.Files{idx}));
    warpedImage = imwarp(I, tforms(idx), OutputView=panoramaView);
    mask = imwarp(true(size(I,1), size(I,2)), tforms(idx), OutputView=panoramaView);
    panorama = imblend(warpedImage, panorama, mask, foregroundopacity=1);
end
end
