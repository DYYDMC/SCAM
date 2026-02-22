buildingDir = uigetdir("Title","Please select the folder to save the intermediate result.");
buildingScene = imageDatastore(buildingDir);

montage(buildingScene.Files)

%%
I = readimage(buildingScene,1);
grayImage = I;
points = detectSURFFeatures(grayImage);
[features,points] = extractFeatures(grayImage,points);

%%
numImages = numel(buildingScene.Files);
tforms(numImages) = projtform2d;
imageSize = zeros(numImages,2);
imageSize(1,:) = size(grayImage);

%%
for n = 2:numImages
    pointsPrevious = points;
    featuresPrevious = features;
        
    I = readimage(buildingScene, n);
    grayImage = I ;
    imageSize(n,:) = size(grayImage);
    
    points = detectSURFFeatures(grayImage);
    [features,points] = extractFeatures(grayImage,points);
  
    indexPairs = matchFeatures(features,featuresPrevious,Unique=true);
    matchedPoints = points(indexPairs(:,1), :);
    matchedPointsPrev = pointsPrevious(indexPairs(:,2), :);        
    
    tforms(n) = estgeotform2d(matchedPoints, matchedPointsPrev,...
        "projective",Confidence=99.9,MaxNumTrials=2000);
    
    tforms(n).A = tforms(n-1).A * tforms(n).A; 
end

%%
for idx = 1:numel(tforms)           
    [xlim(idx,:),ylim(idx,:)] = outputLimits(tforms(idx),[1 imageSize(idx,2)],[1 imageSize(idx,1)]);    
end

%%
avgXLim = mean(xlim, 2);
[~,idx] = sort(avgXLim);
centerIdx = floor((numel(tforms)+1)/2);
centerImageIdx = idx(centerIdx);

%%
Tinv = invert(tforms(centerImageIdx));
for idx = 1:numel(tforms)    
    tforms(idx).A = Tinv.A * tforms(idx).A;
end

%%
for idx = 1:numel(tforms)           
    [xlim(idx,:),ylim(idx,:)] = outputLimits(tforms(idx),[1 imageSize(idx,2)],[1 imageSize(idx,1)]);
end
maxImageSize = max(imageSize);

%%
xMin = min([1; xlim(:)]);
xMax = max([maxImageSize(2); xlim(:)]);

yMin = min([1; ylim(:)]);
yMax = max([maxImageSize(1); ylim(:)]);

%%
width  = round(xMax - xMin);
height = round(yMax - yMin);
%%
xLimits = [xMin xMax];
yLimits = [yMin yMax];
panoramaView = imref2d([height width],xLimits,yLimits);

% %%
% panorama = zeros([height width],"like",I);
% for idx = 1:numImages
%     I = readimage(buildingScene,idx);   
%     warpedImage = imwarp(I,tforms(idx),OutputView=panoramaView);                 
%     mask = imwarp(true(size(I,1),size(I,2)),tforms(idx),OutputView=panoramaView);
% 
%     %imblend is basically doing hard overlay → this causes visible seams.
%     panorama = imblend(warpedImage,panorama,mask,foregroundopacity=1);
% end
% 
% imshow(panorama)
%% Warp all images and store them

warpedImages = cell(numImages,1);
warpedMasks  = cell(numImages,1);

for idx = 1:numImages
    I = readimage(buildingScene,idx);   
    warpedImages{idx} = imwarp(I,tforms(idx),OutputView=panoramaView);
    warpedMasks{idx}  = imwarp(true(size(I,1),size(I,2)),...
                               tforms(idx),OutputView=panoramaView);
end

%% Convert to double (important for 16-bit)
for idx = 1:numImages
    warpedImages{idx} = double(warpedImages{idx});
end
     
%% GAIN COMPENSATION

n = numImages;
A = zeros(n,n);
b = zeros(n,1);

for i = 1:n
    for j = i+1:n
        
        overlap = warpedMasks{i} & warpedMasks{j};
        if nnz(overlap) < 500
            continue;
        end
        
        Ii = warpedImages{i}(overlap);
        Ij = warpedImages{j}(overlap);
        
        mi = mean(Ii);
        mj = mean(Ij);
        
        A(i,i) = A(i,i) + mi^2;
        A(j,j) = A(j,j) + mj^2;
        A(i,j) = A(i,j) - mi*mj;
        A(j,i) = A(j,i) - mi*mj;
    end
end

% Fix first image gain = 1
A(1,:) = 0;
A(1,1) = 1;
b(1) = 1;

gains = A\b;

%% Apply gains
for idx = 1:n
    warpedImages{idx} = warpedImages{idx} * gains(idx);
end
   
%% MULTI-BAND BLENDING

levels = 6;% panorama-size dependent, 5-7 works for 16bit img

% Build pyramids
for i = 1:numImages
    L{i} = buildLaplacianPyramid(warpedImages{i}, levels);
    W{i} = buildGaussianPyramid(double(warpedMasks{i}), levels);
end

% Blend each level
for l = 1:levels
    num = 0;
    den = 0;
    
    for i = 1:numImages
        num = num + L{i}{l} .* W{i}{l};
        den = den + W{i}{l};
    end
    
    blended{l} = num ./ (den + eps);
end

% Collapse pyramid
panorama = blended{levels};

for l = levels-1:-1:1
    panorama = imresize(panorama, size(blended{l}));
    panorama = panorama + blended{l};
end

%% Convert back to 16-bit
panorama = uint16(max(min(panorama,65535),0));
%% save intermediate panorama
dir = uigetdir("Title","Please select the folder to save the intermediate result.");

imwrite(panorama, fullfile(dir, sprintf('panorama_scriptGenBlended_uv.tiff')));
%%
function G = buildGaussianPyramid(img, levels)

G = cell(levels,1);
G{1} = img;

for l = 2:levels
    G{l} = imgaussfilt(G{l-1},2);
    G{l} = imresize(G{l},0.5);
end
end
%%
function L = buildLaplacianPyramid(img, levels)

G = buildGaussianPyramid(img, levels);
L = cell(levels,1);

for l = 1:levels-1
    up = imresize(G{l+1}, size(G{l}));
    L{l} = G{l} - up;
end

L{levels} = G{levels};
end