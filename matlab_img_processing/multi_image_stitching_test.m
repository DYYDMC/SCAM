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

%%
panorama = zeros([height width],"like",I);
for idx = 1:numImages
    I = readimage(buildingScene,idx);   
    warpedImage = imwarp(I,tforms(idx),OutputView=panoramaView);                 
    mask = imwarp(true(size(I,1),size(I,2)),tforms(idx),OutputView=panoramaView);

    %imblend is basically doing hard overlay → this causes visible seams.
    panorama = imblend(warpedImage,panorama,mask,foregroundopacity=1);
end

imshow(panorama)
%% save intermediate panorama
dir = uigetdir("Title","Please select the folder to save the intermediate result.");

imwrite(panorama, fullfile(dir, sprintf('panorama_scriptGen_uv.tiff')));