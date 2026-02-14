% load the roi img (Green channel out of .raw)
im0=imread("g_roi2026_G.tiff");
%im0=imread("uv_roi_2026_new_B.tiff");

% generate a binary mask
mask0 = imbinarize(im0,0.12);

% convert logical to uint8
mask0_uint8=uint8(mask0*255);

% apply a Gaussian filter
mask0_gauss = imgaussfilt(mask0_uint8,20);

% dilate the mask
se_dila=strel('square',5);
mask0_dilate=imdilate(mask0_gauss,se_dila);

% erode the mask
se_erod=strel('square',30);
mask0_erod=imerode(mask0_dilate,se_erod);

% preview
montage({mask0_uint8,mask0_gauss,mask0_dilate,mask0_erod});

% find the center 
[center_green,radius_green]=imfindcircles(mask0_erod,[900,1200]);
cam0_mask=circles2mask(center_green, radius_green, [3040,4056]);
save('cam0_mask_green_specific.mat',"cam0_mask");
save('cam0_roi_center.mat',"center_green");
save('cam0_roi_radius.mat',"radius_green");