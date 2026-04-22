cam1='/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cam1_gain8_660ms_12_tilt3_B.tiff';
cam0='/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cam0_gain1.12_48ms_12_tilt3_G.tiff';

%flip the cam0 mask first
cam0_circle_mask = load("cam0_mask90.mat").circle_mask;
cam0_circle_mask = fliplr(cam0_circle_mask);

cam1_circle_mask = load("cam1_mask95.mat").circle_mask;

img1 = imread(cam1);
img1_masked = img1;
img1_masked(~cam1_circle_mask) = 0;

img0 = imread(cam0);
img0_masked = img0;

img0_masked(~cam0_circle_mask) = 0;
%montage({img0_masked,img1_masked});

%imwrite(img0_masked, '/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_img0.tiff');
%imwrite(img1_masked, '/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_img1.tiff');
%%
% 1. Crop to bounding box of mask
props = regionprops(cam0_circle_mask, 'BoundingBox');
bb = round(props(1).BoundingBox); % choose appropriate region if multiple
r1 = bb(2); r2 = r1+bb(4)-1;
c1 = bb(1); c2 = c1+bb(3)-1;
sub =img0_masked(r1:r2, c1:c2);
subMask = cam0_circle_mask(r1:r2, c1:c2);
%%
% 2. Fill outside pixels with a neutral value (median of inside pixels)
fillVal = median(sub(subMask), 'omitnan');
subFilled = sub;
subFilled(~subMask) = fillVal;
%%

% 3. Apply CLAHE to the filled crop
procSub = adapthisteq(subFilled);  % adjust options if needed
%%
% 4. Restore outside pixels to original values (e.g., zero)
procSub(~subMask) = sub(~subMask);
imwrite(procSub, '/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_adapthisteq_img0.tiff');
clear procSub;
% %%
% % 5. Paste processed crop back into image
% J = img0_masked;
% J(r1:r2, c1:c2) = procSub;


%%
% 1. Crop to bounding box of mask
props = regionprops(cam1_circle_mask, 'BoundingBox');
bb = round(props(1).BoundingBox); % choose appropriate region if multiple
r1 = bb(2); r2 = r1+bb(4)-1;
c1 = bb(1); c2 = c1+bb(3)-1;
sub =img1_masked(r1:r2, c1:c2);
subMask = cam1_circle_mask(r1:r2, c1:c2);
%%
% 2. Fill outside pixels with a neutral value (median of inside pixels)
fillVal = median(sub(subMask), 'omitnan');
subFilled = sub;
subFilled(~subMask) = fillVal;
%%
% 3. Apply CLAHE to the filled crop
procSub = adapthisteq(subFilled);  % adjust options if needed
%%
% 4. Restore outside pixels to original values (e.g., zero)
procSub(~subMask) = sub(~subMask);
imwrite(procSub, '/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_adapthisteq_img1.tiff');