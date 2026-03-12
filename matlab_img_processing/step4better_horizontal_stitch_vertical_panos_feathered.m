%% Better step4: horizontal stitch for left/right pan_*_vertical.tiff with feathered blend
% Output is separated from original step4:
%   PANO_*/panoramas/horizontal_from_vertical_feathered/left_full_pano_feathered.tiff
%   PANO_*/panoramas/horizontal_from_vertical_feathered/right_full_pano_feathered.tiff

panoDir = uigetdir("Title", "Select a PANO_* folder");
if isequal(panoDir, 0)
    error("No folder selected.");
end

defaultRoot = fullfile(panoDir, "RGB_overlay_mix", "vertical");
if isfolder(defaultRoot)
    sideRoot = defaultRoot;
else
    sideRoot = panoDir;
end

outDir = fullfile(panoDir, "panoramas", "horizontal_from_vertical_feathered");
if ~isfolder(outDir), mkdir(outDir); end

% Constrain feathering to a narrow seam band inside overlap.
EnableConstrainedFeather = true;
BandWidthPx = 40;

for sideName = ["left", "right"]
    sidePath = fullfile(sideRoot, sideName);
    if ~isfolder(sidePath)
        fprintf("Skipping missing folder: %s\n", sidePath);
        continue;
    end

    outPath = fullfile(outDir, sprintf("%s_full_pano_feathered_bandwidth40.tiff", sideName));
    if isfile(outPath)
        fprintf("Skipping existing: %s\n", outPath);
        continue;
    end

    try
        panorama = stitch_one_side_folder_feathered(sidePath, sideName, EnableConstrainedFeather, BandWidthPx);
        imwrite(panorama, outPath);
        fprintf("Saved: %s\n", outPath);
    catch ME
        fprintf(2, "Failed %s: %s\n", sideName, ME.message);
    end
end

function panorama = stitch_one_side_folder_feathered(sidePath, sideName, enableConstrained, bandWidthPx)
ds = imageDatastore(sidePath, "IncludeSubfolders", false, "FileExtensions", {'.tif', '.tiff'});
files = ds.Files;
if isempty(files), error("No TIFF files in %s", sidePath); end

isPanVertical = ~cellfun('isempty', regexp(files, 'pan_-?[0-9]+_vertical\.tiff?$', 'once'));
files = files(isPanVertical);
tokens = regexp(files, 'pan_(-?[0-9]+)_vertical\.tiff?$', 'tokens', 'once');
if isempty(files), error("No pan_*_vertical TIFF files in %s", sidePath); end

nums = nan(size(tokens));
for k = 1:numel(tokens)
    if ~isempty(tokens{k}), nums(k) = str2double(tokens{k}{1}); end
end

if sideName == "left", sortDir = "descend"; else, sortDir = "ascend"; end
[~, order] = sort(nums, sortDir, "MissingPlacement", "last");
files = files(order);
if numel(files) < 2, error("Need at least 2 pan_*_vertical TIFF files in %s", sidePath); end

N = numel(files);
images = cell(N,1); grayImages = cell(N,1); imageSize = zeros(N,2);
for i = 1:N
    I = crop_pano_to_largest_valid_rect(imread(files{i}));
    images{i} = I;
    grayImages{i} = im2gray(I);
    imageSize(i,:) = [size(I,1), size(I,2)];
end

points = detectSURFFeatures(grayImages{1});
[features, points] = extractFeatures(grayImages{1}, points);
tforms(N) = projtform2d;

for n = 2:N
    pointsPrev = points; featuresPrev = features;
    points = detectSURFFeatures(grayImages{n});
    [features, points] = extractFeatures(grayImages{n}, points);
    pairs = matchFeatures(features, featuresPrev, Unique=true);
    matched = points(pairs(:,1), :);
    matchedPrev = pointsPrev(pairs(:,2), :);
    stepT = estimate_tform_with_fallback(matched, matchedPrev, size(pairs,1));
    if isempty(stepT), error("Transform failed between images %d and %d", n-1, n); end
    tforms(n) = stepT;
    tforms(n).A = tforms(n-1).A * tforms(n).A;
end

xlim = zeros(N,2); ylim = zeros(N,2);
for i = 1:N
    [xlim(i,:), ylim(i,:)] = outputLimits(tforms(i), [1 imageSize(i,2)], [1 imageSize(i,1)]);
end
avgX = mean(xlim,2);
[~, idxSort] = sort(avgX);
centerImageIdx = idxSort(floor((N+1)/2));
Tinv = invert(tforms(centerImageIdx));
for i = 1:N, tforms(i).A = Tinv.A * tforms(i).A; end

for i = 1:N
    [xlim(i,:), ylim(i,:)] = outputLimits(tforms(i), [1 imageSize(i,2)], [1 imageSize(i,1)]);
end
maxSize = max(imageSize, [], 1);
xMin = min([1; xlim(:)]); xMax = max([maxSize(2); xlim(:)]);
yMin = min([1; ylim(:)]); yMax = max([maxSize(1); ylim(:)]);
W = round(xMax - xMin); H = round(yMax - yMin);
view = imref2d([H W], [xMin xMax], [yMin yMax]);

warped = cell(N,1); masks = cell(N,1);
for i = 1:N
    I = images{i};
    warped{i} = imwarp(I, tforms(i), OutputView=view);
    masks{i} = imwarp(true(size(I,1), size(I,2)), tforms(i), OutputView=view);
end

panorama = warped{1}; maskPan = masks{1};
for i = 2:N
    if enableConstrained
        [panorama, maskPan] = feather_blend_pair_constrained(panorama, maskPan, warped{i}, masks{i}, bandWidthPx);
    else
        [panorama, maskPan] = feather_blend_pair(panorama, maskPan, warped{i}, masks{i});
    end
end
end

function [out, outMask] = feather_blend_pair(A, maskA, B, maskB)
maskA = logical(maskA); maskB = logical(maskB);
if ndims(A)==2, A = reshape(A,size(A,1),size(A,2),1); end
if ndims(B)==2, B = reshape(B,size(B,1),size(B,2),1); end

wA = bwdist(~maskA); wB = bwdist(~maskB);
wA(~maskA)=0; wB(~maskB)=0;
den = wA + wB; den(den==0)=1;
aA = wA./den; aB = wB./den;
onlyA = maskA & ~maskB; onlyB = maskB & ~maskA;
aA(onlyA)=1; aB(onlyA)=0; aA(onlyB)=0; aB(onlyB)=1;

AD = im2double(A); BD = im2double(B); outD = zeros(size(AD));
for c = 1:size(AD,3), outD(:,:,c) = aA.*AD(:,:,c) + aB.*BD(:,:,c); end

if isa(A,'uint16'), out = im2uint16(outD);
elseif isa(A,'uint8'), out = im2uint8(outD);
else, out = cast(outD, class(A)); end
if size(out,3)==1, out = out(:,:,1); end
outMask = maskA | maskB;
end

function [out, outMask] = feather_blend_pair_constrained(A, maskA, B, maskB, bandWidthPx)
% Feather only in a narrow vertical band around overlap center.
maskA = logical(maskA); maskB = logical(maskB);
if ndims(A)==2, A = reshape(A,size(A,1),size(A,2),1); end
if ndims(B)==2, B = reshape(B,size(B,1),size(B,2),1); end

[H, W, C] = size(A);
overlap = maskA & maskB;
if ~any(overlap(:))
    [out, outMask] = feather_blend_pair(A, maskA, B, maskB);
    return;
end

% Estimate seam x at center of overlap footprint.
colHasOverlap = any(overlap, 1);
xIdx = find(colHasOverlap);
x0 = round((xIdx(1) + xIdx(end)) / 2);

[X, ~] = meshgrid(1:W, 1:H);
bandMask = overlap & (abs(X - x0) <= bandWidthPx);

% Base hard composition outside band: left of seam from A, right from B.
hardFromA = maskA & ~maskB;
hardFromB = maskB & ~maskA;
hardFromA = hardFromA | (overlap & ~bandMask & (X <= x0));
hardFromB = hardFromB | (overlap & ~bandMask & (X > x0));

% Feather only inside band.
wA = bwdist(~maskA); wB = bwdist(~maskB);
wA(~bandMask) = 0; wB(~bandMask) = 0;
den = wA + wB; den(den==0)=1;
aA = wA./den; aB = wB./den;

AD = im2double(A); BD = im2double(B);
outD = zeros(size(AD));
for c = 1:C
    Ac = AD(:,:,c);
    Bc = BD(:,:,c);
    tmp = zeros(H,W);
    tmp(hardFromA) = Ac(hardFromA);
    tmp(hardFromB) = Bc(hardFromB);
    tmp(bandMask) = aA(bandMask).*Ac(bandMask) + aB(bandMask).*Bc(bandMask);
    outD(:,:,c) = tmp;
end

if isa(A,'uint16'), out = im2uint16(outD);
elseif isa(A,'uint8'), out = im2uint8(outD);
else, out = cast(outD, class(A)); end
if size(out,3)==1, out = out(:,:,1); end
outMask = maskA | maskB;
end

function tform = estimate_tform_with_fallback(movingPts, fixedPts, numPairs)
tform = [];
if numPairs < 2, return; end
modelOrder = ["projective", "affine", "similarity", "rigid"];
minPairs = [4, 3, 2, 2];
for m = 1:numel(modelOrder)
    if numPairs < minPairs(m), continue; end
    try
        tform = estgeotform2d(movingPts, fixedPts, modelOrder(m), Confidence=99.9, MaxNumTrials=2000);
        return;
    catch
    end
end
end
