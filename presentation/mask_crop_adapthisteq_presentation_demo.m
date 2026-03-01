%% Presentation demo for mask/crop/adapthisteq pipeline (single paired frame)
% Run this script from any location; it resolves paths relative to this file.

scriptDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(scriptDir);
maskDir = fullfile(repoRoot, 'matlab_roi_extraction');

cam0Path = fullfile(scriptDir, 'cam0_gain1.12_87ms_46_G.tiff');
cam1Path = fullfile(scriptDir, 'cam1_gain8.0_1000ms_46_B.tiff');

if ~isfile(cam0Path) || ~isfile(cam1Path)
    error('Required TIFF files are missing in %s', scriptDir);
end
if ~isfile(fullfile(maskDir, 'cam0_mask.mat')) || ~isfile(fullfile(maskDir, 'cam1_mask.mat'))
    error('cam0_mask.mat or cam1_mask.mat not found in %s', maskDir);
end

img0 = imread(cam0Path);
img1 = imread(cam1Path);

%% 1) Unprocessed
figure('Name', 'Unprocessed');
show_two_with_labels(img0, img1, 'unprocessed');

%% Load circle and square masks
cam0Mask = load(fullfile(maskDir, 'cam0_mask.mat'));
cam1Mask = load(fullfile(maskDir, 'cam1_mask.mat'));

circleMask0 = fliplr(cam0Mask.circle_mask); % keep consistent with cam0 handling
circleMask1 = cam1Mask.circle_mask;

squareMask0 = fliplr(cam0Mask.square_mask);
squareMask1 = cam1Mask.square_mask;

%% 2) Circle masked
circleMasked0 = img0;
circleMasked1 = img1;
circleMasked0(~circleMask0) = 0;
circleMasked1(~circleMask1) = 0;

imwrite(circleMasked0, fullfile(scriptDir, 'circle_masked_cam0.tiff'));
imwrite(circleMasked1, fullfile(scriptDir, 'circle_masked_cam1.tiff'));

figure('Name', 'Circle Masked');
show_two_with_labels(circleMasked0, circleMasked1, 'Circle\_masked\_images');

%% 2.5) Overlay: circle + concentric square on circle-masked images
overlay0 = make_mask_overlay(circleMasked0, circleMask0, squareMask0);
overlay1 = make_mask_overlay(circleMasked1, circleMask1, squareMask1);

figure('Name', 'Circle-Square Overlay');
show_two_with_labels(overlay0, overlay1, 'Image superimposed w. masks');

%% 3) Square mask + concentric square crop
squareMasked0 = img0;
squareMasked1 = img1;
squareMasked0(~squareMask0) = 0;
squareMasked1(~squareMask1) = 0;

bb0 = ceil(regionprops(squareMask0, 'BoundingBox').BoundingBox);
bb1 = ceil(regionprops(squareMask1, 'BoundingBox').BoundingBox);

squareCrop0 = squareMasked0(bb0(2):(bb0(2)+bb0(4)-1), bb0(1):(bb0(1)+bb0(3)-1), :);
squareCrop1 = squareMasked1(bb1(2):(bb1(2)+bb1(4)-1), bb1(1):(bb1(1)+bb1(3)-1), :);

imwrite(squareCrop0, fullfile(scriptDir, 'square_masked_cam0.tiff'));
imwrite(squareCrop1, fullfile(scriptDir, 'square_masked_cam1.tiff'));

figure('Name', 'Square Crops');
show_two_with_labels(squareCrop0, squareCrop1, 'Concentric square-masked crops');

figure('Name', 'Square Crop Histograms');
plot_paired_hist(squareCrop0, squareCrop1, ...
    'SquareCrop\_green\_image', ...
    'SquareCrop\_UV\_image');

%% 4) adapthisteq on square crops
adap0 = adapthisteq(squareCrop0);
adap1 = adapthisteq(squareCrop1);

imwrite(adap0, fullfile(scriptDir, 'adapthisteq_square_masked_cam0.tiff'));
imwrite(adap1, fullfile(scriptDir, 'adapthisteq_square_masked_cam1.tiff'));

figure('Name', 'Adapthisteq Square Crops');
show_two_with_labels(adap0, adap1, 'Adapthisteq() square-masked images');

figure('Name', 'Adapthisteq Histograms');
plot_paired_hist(adap0, adap1, ...
    'Adapthisteq\_Green\_image', ...
    'Adapthisteq\_UV\_image');

function plot_paired_hist(imgCam0, imgCam1, titleCam0, titleCam1)
% Use same bins/ranges for both histograms so comparisons are meaningful.
[counts0, bins] = imhist(imgCam0, 256);
[counts1, bins1] = imhist(imgCam1, 256);

yMax = max([counts0(:); counts1(:)]);
xMin = min([bins(:); bins1(:)]);
xMax = max([bins(:); bins1(:)]);

ax1 = subplot(1,2,1);
bar(bins, counts0, 1, 'FaceColor', [0.10 0.60 0.10], 'EdgeColor', 'none');
title(titleCam0);
xlabel('Intensity'); ylabel('Count');
xlim([xMin xMax]); ylim([0 yMax]);

ax2 = subplot(1,2,2);
bar(bins1, counts1, 1, 'FaceColor', [0.55 0.25 0.70], 'EdgeColor', 'none');
title(titleCam1);
xlabel('Intensity'); ylabel('Count');
xlim([xMin xMax]); ylim([0 yMax]);

linkaxes([ax1 ax2], 'xy');
end

function show_two_with_labels(imgCam0, imgCam1, mainTitleText)
tiledlayout(1,2, 'Padding', 'compact', 'TileSpacing', 'compact');
nexttile; imshow(imgCam0); title('Green\_image');
nexttile; imshow(imgCam1); title('UV\_image');
sgtitle(mainTitleText);
end

function outRgb = make_mask_overlay(baseImg, circleMask, squareMask)
base = mat2gray(baseImg);
outRgb = cat(3, base, base, base);

% circle and square boundaries in white (thick + hard overlay)
circleEdge = bwperim(circleMask);
squareEdge = bwperim(squareMask);
% Make boundaries thicker by increasing the dilation radius.
% Change the '4' to a larger integer to get thicker edges (e.g., 8).
dilateRadius = 8; % adjust this value to control thickness
circleEdge = imdilate(circleEdge, strel('disk', dilateRadius, 0));
squareEdge = imdilate(squareEdge, strel('disk', dilateRadius, 0));

% Hard overwrite for maximum visibility.
overlayEdge = circleEdge | squareEdge;
outRgb(:,:,1) = max(outRgb(:,:,1), 1.0 * overlayEdge);
outRgb(:,:,2) = max(outRgb(:,:,2), 1.0 * overlayEdge);
outRgb(:,:,3) = max(outRgb(:,:,3), 1.0 * overlayEdge);
end
