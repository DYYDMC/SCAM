I = imread('panorama_LR_stitched.tiff');        % RGB image (MxNx3)
G = double(I(:,:,2));
B = double(I(:,:,3));

% Signed difference (positive = R brighter than G)
diff_signed_GB = G - B;
diff_signed_BG = B - G;

% Absolute difference (magnitude of luminance difference)
diff_abs = abs(diff_signed);

% Display
figure;
subplot(2,2,1), imshow(I), title('RGUV image')

subplot(2,2,2)
imagesc(mat2gray(diff_abs)), axis image off
title('Absolute G-UV (normalized)')
colormap(gca, hot); colorbar

subplot(2,2,3)
imagesc(mat2gray(diff_signed_GB)), axis image off
title('Signed G-UV (normalized)')
colormap(gca, hot); colorbar

subplot(2,2,4)
imagesc(mat2gray(diff_signed_BG)), axis image off
title('Signed UV-G (normalized)')
colormap(gca, hot); colorbar


