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
montage({img0, img1});
title('unprocessed');

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
montage({circleMasked0, circleMasked1});
title('cropped using the largest circle');

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
montage({squareCrop0, squareCrop1});
title('concentric square crops');

figure('Name', 'Square Crop Histograms');
plot_paired_hist(squareCrop0, squareCrop1, ...
    'imhist(square\_masked\_cam0)', ...
    'imhist(square\_masked\_cam1)');

%% 4) adapthisteq on square crops
adap0 = adapthisteq(squareCrop0);
adap1 = adapthisteq(squareCrop1);

imwrite(adap0, fullfile(scriptDir, 'adapthisteq_square_masked_cam0.tiff'));
imwrite(adap1, fullfile(scriptDir, 'adapthisteq_square_masked_cam1.tiff'));

figure('Name', 'Adapthisteq Square Crops');
montage({adap0, adap1});
title('adapthisteq on concentric square crops');

figure('Name', 'Adapthisteq Histograms');
plot_paired_hist(adap0, adap1, ...
    'imhist(adapthisteq\_square\_masked\_cam0)', ...
    '');

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
