%% load masks

cam1_mask=load("rois_mat/cam1_mask_uv_specific.mat").cam1_mask;
center_uv = load('rois_mat/cam1_roi_center.mat').center_uv;
cam1_mask_radius= load('rois_mat/cam1_roi_radius.mat').radius_uv;

cam1_center_x=center_uv(1);cam1_center_y=center_uv(2);
cam1_radius=cam1_mask_radius;
%cam1_mask=flipud(cam1_mask);
%% make a square mask
reduceFactor=.8;
%% the largest concentric square that fit inside the circular mask
half = round(cam1_radius/sqrt(2));

%%
half=round(half*reduceFactor);
[H,W]=size(cam1_mask);

r1 = max(1, round(cam1_center_y - half));
r2 = min(H, round(cam1_center_y + half));
c1 = max(1, round(cam1_center_x - half));
c2 = min(W, round(cam1_center_x + half));
%% create the mask
cam1_square_mask = false(H, W);
cam1_square_mask(r1:r2, c1:c2) = true;
%%
mfile2.center_x=cam1_center_x;
mfile2.center_y=cam1_center_y;
mfile2.radius=cam1_radius;
mfile2.half=half;
mfile2.square_mask=cam1_square_mask;
mfile2.circle_mask=cam1_mask;
%%
save('cam1_mask.mat','-struct','mfile2')
%%
imshowpair(cam1_square_mask,cam1_mask)