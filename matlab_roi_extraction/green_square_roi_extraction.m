%% load masks

cam0_mask=load("rois_mat/cam0_mask_green_specific.mat").cam0_mask;
center_green = load('rois_mat/cam0_roi_center.mat').center_green;
cam0_mask_radius= load('rois_mat/cam0_roi_radius.mat').radius_green;

cam0_center_x=cam0_mask_center(1);cam0_center_y=cam0_mask_center(2);
cam0_radius=cam0_mask_radius;

%% make a square mask
half = round(cam0_radius/sqrt(2));
[H,W]=size(cam0_mask);

r1 = max(1, round(cam0_center_y - half));
r2 = min(H, round(cam0_center_y + half));
c1 = max(1, round(cam0_center_x - half));
c2 = min(W, round(cam0_center_x + half));

%% create the mask
cam0_square_mask = false(H, W);
cam0_square_mask(r1:r2, c1:c2) = true;
save('cam0_square_mask_green_specific.mat',"cam0_square_mask");
save('cam0_roi_center.mat',"center_green");
save('cam0_squareroi_half.mat',"half");

imshowpair(cam0_square_mask,cam0_mask)