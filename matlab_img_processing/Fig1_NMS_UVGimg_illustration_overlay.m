%%
img1_prepro='/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_adapthisteq_img1.tiff';
img0_prepro='/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/cirle_masked_adapthisteq_img0.tiff';


imgGreen = imread(img0_prepro); % moving image to be warped
imgUV = imread(img1_prepro);       % fixed/reference image
%%
% Same homography logic used in step2_mono2RGB_homography.mlx
regOut = registerImages_pano20260225121745(imgGreen, imgUV);
warpedGreen = regOut.RegisteredImage;

if ndims(imgUV) == 3
    uvMono = imgUV(:,:,1);
else
    uvMono = imgUV;
end
if ndims(warpedGreen) == 3
    greenMono = warpedGreen(:,:,1);
else
    greenMono = warpedGreen;
end

[h, w] = size(uvMono);
rgbOut = zeros([h, w, 3], "like", uvMono);
rgbOut(:,:,2) = greenMono; % green channel
rgbOut(:,:,3) = uvMono;    % blue channel
%%
imwrite(rgbOut,'/Users/dengyuyao/Desktop/PhD/NMS2026/Fig1/UVG_img_illustration/ONE_SCAM_20260317_064234/overlaid.tiff' );
%montage({greenMono,uvMono,rgbOut}, 'Size', [1 3]);