im1=imread('uv_roi_2026_new_B.tiff');

mask1=imbinarize(im1,0.08);

mask1_uint8=uint8(mask1*255);

mask1_gauss = imgaussfilt(mask1_uint8,50);

se_dila=strel('square',5);

mask1_dilate=imdilate(mask1_gauss,se_dila);

[center_uv,radius_uv]=imfindcircles(mask1_dilate,[900,1200]);
cam1_mask=circles2mask(center_uv, radius_uv, [3040,4056]);
save('cam1_mask_uv_specific.mat',"cam1_mask");
save('cam1_roi_center.mat',"center_uv");
save('cam1_roi_radius.mat',"radius_uv");