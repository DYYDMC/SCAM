function meadow_texture_compare_ui()
% Meadow texture comparison: 350 nm (B channel) vs 480 nm (G channel)
% Uses local-window GLCM + local variance with UI file selection.

clc; close all;

%% 1) UI: select image file
[file, path] = uigetfile( ...
    {'*.tif;*.tiff;*.png;*.jpg;*.jpeg','Image Files (*.tif,*.tiff,*.png,*.jpg)'; ...
     '*.*','All Files (*.*)'}, ...
    'Select registered RGB image (G=480nm, B=350nm)');

if isequal(file,0)
    disp('No file selected. Exiting.');
    return;
end

imgPath = fullfile(path, file);
rgb = imread(imgPath);

if size(rgb,3) < 3
    error('Image must be RGB with at least 3 channels.');
end

% Convert to double [0,1]
rgb = im2double(rgb);

% Channel assignment per your setup
I480 = rgb(:,:,2); % G channel = 480 nm
I350 = rgb(:,:,3); % B channel = 350 nm

%% 2) Parameters (quick defaults)
windowSizes = [64, 128];
offsets = [0 1; -1 1; -1 0; -1 -1]; % 0,45,90,135 deg
numLevels = 16; % GLCM gray levels

%% 3) Global summary (whole image)
fprintf('\n=== Global Summary ===\n');
global480 = glcm_features_single(I480, offsets, numLevels);
global350 = glcm_features_single(I350, offsets, numLevels);

fprintf('480nm: Contrast=%.4f  Homogeneity=%.4f  Energy=%.4f  Entropy=%.4f  Variance=%.4f\n', ...
    global480.contrast, global480.homogeneity, global480.energy, global480.entropy, var(I480(:)));
fprintf('350nm: Contrast=%.4f  Homogeneity=%.4f  Energy=%.4f  Entropy=%.4f  Variance=%.4f\n', ...
    global350.contrast, global350.homogeneity, global350.energy, global350.entropy, var(I350(:)));

%% 4) Local window analysis + maps
for w = windowSizes
    step = w/2; % 50% overlap
    [maps480, maps350, centersX, centersY] = local_texture_maps(I480, I350, w, step, offsets, numLevels);

    % Difference maps (350 - 480)
    dContrast    = maps350.contrast    - maps480.contrast;
    dHomogeneity = maps350.homogeneity - maps480.homogeneity;
    dEnergy      = maps350.energy      - maps480.energy;
    dEntropy     = maps350.entropy     - maps480.entropy;
    dVar         = maps350.variance    - maps480.variance;

    % Plot
    figure('Name', sprintf('Texture Maps (Window %d)', w), 'Color', 'w', 'Position', [100 100 1400 800]);

    subplot(2,4,1); imagesc(maps480.contrast); axis image off; colorbar; title(sprintf('480 Contrast (w=%d)',w));
    subplot(2,4,2); imagesc(maps350.contrast); axis image off; colorbar; title(sprintf('350 Contrast (w=%d)',w));
    subplot(2,4,3); imagesc(dContrast); axis image off; colorbar; title('\\Delta Contrast (350-480)');
    subplot(2,4,4); imagesc(maps350.variance - maps480.variance); axis image off; colorbar; title('\\Delta Variance');

    subplot(2,4,5); imagesc(maps480.homogeneity); axis image off; colorbar; title('480 Homogeneity');
    subplot(2,4,6); imagesc(maps350.homogeneity); axis image off; colorbar; title('350 Homogeneity');
    subplot(2,4,7); imagesc(dHomogeneity); axis image off; colorbar; title('\\Delta Homogeneity');
    subplot(2,4,8); imagesc(dEntropy); axis image off; colorbar; title('\\Delta Entropy');

    % Print quick stats
    fprintf('\n=== Local Summary (window=%d, step=%d) ===\n', w, step);
    fprintf('Mean \\DeltaContrast:    %.4f\n', mean(dContrast(:), 'omitnan'));
    fprintf('Mean \\DeltaHomogeneity: %.4f\n', mean(dHomogeneity(:), 'omitnan'));
    fprintf('Mean \\DeltaEnergy:      %.4f\n', mean(dEnergy(:), 'omitnan'));
    fprintf('Mean \\DeltaEntropy:     %.4f\n', mean(dEntropy(:), 'omitnan'));
    fprintf('Mean \\DeltaVariance:    %.4f\n', mean(dVar(:), 'omitnan'));

    % Optional overlay of sampling centers
    figure('Name', sprintf('Sampling Grid (Window %d)', w), 'Color', 'w');
    imshow(cat(3, zeros(size(I480)), I480, I350), []);
    title(sprintf('False color (G=480, B=350) with window centers, w=%d', w)); hold on;
    plot(centersX, centersY, 'r.', 'MarkerSize', 8);
    hold off;
end

disp('Done.');

end

%% ---------------- Helper functions ----------------

function [maps480, maps350, centersX, centersY] = local_texture_maps(I480, I350, w, step, offsets, numLevels)
[H, W] = size(I480);

xStarts = 1:step:(W - w + 1);
yStarts = 1:step:(H - w + 1);

ny = numel(yStarts);
nx = numel(xStarts);

maps480.contrast = nan(ny, nx);
maps480.homogeneity = nan(ny, nx);
maps480.energy = nan(ny, nx);
maps480.entropy = nan(ny, nx);
maps480.variance = nan(ny, nx);

maps350 = maps480;

centersX = zeros(ny*nx,1);
centersY = zeros(ny*nx,1);
k = 1;

for iy = 1:ny
    for ix = 1:nx
        y = yStarts(iy);
        x = xStarts(ix);

        p480 = I480(y:y+w-1, x:x+w-1);
        p350 = I350(y:y+w-1, x:x+w-1);

        f480 = glcm_features_single(p480, offsets, numLevels);
        f350 = glcm_features_single(p350, offsets, numLevels);

        maps480.contrast(iy,ix) = f480.contrast;
        maps480.homogeneity(iy,ix) = f480.homogeneity;
        maps480.energy(iy,ix) = f480.energy;
        maps480.entropy(iy,ix) = f480.entropy;
        maps480.variance(iy,ix) = var(p480(:));

        maps350.contrast(iy,ix) = f350.contrast;
        maps350.homogeneity(iy,ix) = f350.homogeneity;
        maps350.energy(iy,ix) = f350.energy;
        maps350.entropy(iy,ix) = f350.entropy;
        maps350.variance(iy,ix) = var(p350(:));

        centersX(k) = x + (w-1)/2;
        centersY(k) = y + (w-1)/2;
        k = k + 1;
    end
end
end

function feat = glcm_features_single(I, offsets, numLevels)
% Quantize to fixed gray levels for stable GLCM
Iu = im2uint8(mat2gray(I));
Iq = gray2ind(Iu, numLevels);

glcm = graycomatrix(Iq, ...
    'NumLevels', numLevels, ...
    'Offset', offsets, ...
    'Symmetric', true);

stats = graycoprops(glcm, {'Contrast','Homogeneity','Energy'});

% Average over offsets
feat.contrast = mean(stats.Contrast);
feat.homogeneity = mean(stats.Homogeneity);
feat.energy = mean(stats.Energy);

% Entropy from normalized GLCM (per offset then averaged)
nOff = size(glcm,3);
ent = zeros(nOff,1);
for i = 1:nOff
    P = glcm(:,:,i);
    P = P / sum(P(:) + eps);
    ent(i) = -sum(P(:) .* log2(P(:) + eps));
end
feat.entropy = mean(ent);
end
