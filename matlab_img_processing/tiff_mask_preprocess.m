%% load images
dir = uigetdir("Title","Please select the Concrete Registration folder in your course files.");
%%
imds = imageDatastore(dir, 'FileExtensions', {'.tif', '.tiff'}, 'IncludeSubfolders', false);

files = imds.Files;   % cell array of full paths

% Use \d+ or \d{1,3} to match 0..100 explicitly
tokens = regexp(files, '(?i)_([0-9]{1,3})_B\.tiff?$', 'tokens', 'once');

nums = nan(size(tokens));
for k = 1:numel(tokens)
    if ~isempty(tokens{k})
        nums(k) = str2double(tokens{k}{1});
    end
end

% Sort by the numeric index (NaN go to end)
[~, order] = sort(nums, 'ascend', 'MissingPlacement', 'last');

% Reorder datastore (replace Files)
imds.Files = files(order);
%%
disp(imds.Files);
numFiles = numel(imds.Files);
%% Load mask
% this was the circular mask
% cam1_mask=load("cam1_mask_uv_specific.mat").cam1_mask;

% this applies the square mask
%cam_mask=load("cam1_square_mask_uv_specific.mat").cam1_square_mask;
cam_mask=load("cam0_square_mask_green_specific.mat").cam0_square_mask;
cam_mask =fliplr(cam_mask);
%cam1_mask=fliplr(cam1_mask); % due to roi 
%cam1_mask=flipud(cam1_mask);
%%
ii = 0;
numFiles = numel(imds.Files);
for k = 1:numFiles
    ii = ii + 1;
    img = readimage(imds, k);    % safe: reads kth image
    img = fliplr(img);
    img_masked = img;
    img_masked(~cam_mask) = 0;
    img_maskedd_flipped_adjusted = imadjust(img_masked, [], [], 0.5);

    props = regionprops(cam_mask, 'BoundingBox');
    bb = ceil(props(1).BoundingBox);   % use props(1) if multiple regions
    cropped_ = img_maskedd_flipped_adjusted(bb(2):(bb(2)+bb(4)-1), ...
                                            bb(1):(bb(1)+bb(3)-1), :);

    imwrite(cropped_, fullfile(dir, sprintf('preproed_cropped_green_%d.tiff', ii)));
end