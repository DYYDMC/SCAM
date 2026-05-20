function meadow_delta_variance_batch_ui()
% Batch delta-variance analysis for registered RGB TIFF files.
% Assumes G channel = 480 nm and B channel = 350 nm.
% For each TIFF, saves a 2x3 figure:
% Row 1: RGB overlay, Green channel, Blue channel
% Row 2: Delta variance (B-G), Green variance, Blue variance

clc; close all;

%% Select input folder
inputDir = uigetdir(pwd, 'Select folder containing TIFF files');
if isequal(inputDir, 0)
    disp('No folder selected. Exiting.');
    return;
end

%% Create output folder
outDir = fullfile(inputDir, 'delta_variance_results');
if ~exist(outDir, 'dir')
    mkdir(outDir);
end

%% Parameters
w = 16;
step = 8; % 50% overlap

%% Gather TIFF files
filesTif = dir(fullfile(inputDir, '*.tif'));
filesTiff = dir(fullfile(inputDir, '*.tiff'));
files = [filesTif; filesTiff];

if isempty(files)
    fprintf('No TIFF files found in: %s\n', inputDir);
    return;
end

fprintf('Found %d TIFF files. Processing...\n', numel(files));

for k = 1:numel(files)
    inPath = fullfile(files(k).folder, files(k).name);
    [~, baseName, ~] = fileparts(files(k).name);

    try
        rgb = imread(inPath);

        if ndims(rgb) < 3 || size(rgb, 3) < 3
            warning('Skipping %s (not RGB with >=3 channels).', files(k).name);
            continue;
        end

        rgbd = im2double(rgb);
        rgbd=crop_pano_to_largest_valid_rect(rgbd);
        G = rgbd(:,:,2); % 480 nm
        B = rgbd(:,:,3); % 350 nm

        [varG, varB] = local_variance_maps(G, B, w, step);
        dVar = varB - varG;

        fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1400 800]);

        subplot(2,3,1);
        imshow(rgbd, []);
        title('Overlaid RGB');

        subplot(2,3,2);
        imshow(G, []);
        title('Green (480 nm)');

        subplot(2,3,3);
        imshow(B, []);
        title('Blue (350 nm)');

        subplot(2,3,4);
        imagesc(dVar);
        axis image off;
        colorbar;
        title(sprintf('Delta Variance (B-G), w=%d', w));

        subplot(2,3,5);
        imagesc(varG);
        axis image off;
        colorbar;
        title(sprintf('Green Variance, w=%d', w));

        subplot(2,3,6);
        imagesc(varB);
        axis image off;
        colorbar;
        title(sprintf('Blue Variance, w=%d', w));

        sgtitle(sprintf('%s', files(k).name), 'Interpreter', 'none');

        outPng = fullfile(outDir, [baseName '_delta_variance_w16.png']);
        exportgraphics(fig, outPng, 'Resolution', 200);

        close(fig);
        fprintf('[%d/%d] Saved: %s\n', k, numel(files), outPng);

    catch ME
        warning('Failed on %s: %s', files(k).name, ME.message);
    end
end

disp('Batch processing complete.');

end

function [varG, varB] = local_variance_maps(G, B, w, step)
[H, W] = size(G);

xStarts = 1:step:(W - w + 1);
yStarts = 1:step:(H - w + 1);

ny = numel(yStarts);
nx = numel(xStarts);

varG = nan(ny, nx);
varB = nan(ny, nx);

for iy = 1:ny
    y = yStarts(iy);
    for ix = 1:nx
        x = xStarts(ix);

        patchG = G(y:y+w-1, x:x+w-1);
        patchB = B(y:y+w-1, x:x+w-1);

        varG(iy, ix) = var(patchG(:));
        varB(iy, ix) = var(patchB(:));
    end
end
end
