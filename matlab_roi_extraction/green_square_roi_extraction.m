%% load masks

cam0_mask=load("rois_mat/cam0_mask_green_specific.mat").cam0_mask;
center_cam0 = load('rois_mat/cam0_roi_center.mat').center_green;
cam0_mask_radius= load('rois_mat/cam0_roi_radius.mat').radius_green;

cam0_center_x=center_cam0(1);cam0_center_y=center_cam0(2);
cam0_radius=cam0_mask_radius;

%% make a square mask
reduceFactor=.8;
%% the largest concentric square that fit inside the circular mask
half = round(cam0_radius/sqrt(2));

%%
half=round(half*reduceFactor);
[H,W]=size(cam0_mask);

r1 = max(1, round(cam0_center_y - half));
r2 = min(H, round(cam0_center_y + half));
c1 = max(1, round(cam0_center_x - half));
c2 = min(W, round(cam0_center_x + half));

%% create the mask
cam0_square_mask = false(H, W);
cam0_square_mask(r1:r2, c1:c2) = true;
%%
mfile2.center_x=cam0_center_x;
mfile2.center_y=cam0_center_y;
mfile2.radius=cam0_radius;
mfile2.half=half;
mfile2.square_mask=cam0_square_mask;
mfile2.circle_mask=cam0_mask;
%%
save('cam0_mask.mat','-struct','mfile2')
%%
imshowpair(cam0_square_mask,cam0_mask)