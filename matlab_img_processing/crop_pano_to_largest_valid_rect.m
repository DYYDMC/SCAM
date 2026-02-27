function cropped = crop_pano_to_largest_valid_rect(img_l_full)
% CROP_PANO_TO_LARGEST_VALID_RECT Crop input image to largest all-nonzero-green rectangle
%   cropped = CROP_PANO_TO_LARGEST_VALID_RECT(img) returns the cropped image
%   containing the largest axis-aligned rectangle where the green channel is
%   nonzero. Input img can be grayscale or RGB; for RGB the green channel is used.
%
%   Example:
%     cropped = crop_pano_to_largest_valid_rect(imread('tilt_10_left.tiff'));

if nargin == 0 || isempty(img_l_full)
    error('Input image is required.');
end

% Ensure image is at least 2D; extract green channel if RGB, otherwise use the image.
if ndims(img_l_full) == 3
    img_double_Gch = im2double(img_l_full(:,:,2));
else
    img_double_Gch = im2double(img_l_full);
end

mask = img_double_Gch > 0;

[H, W] = size(mask);
heights = zeros(1, W);

bestArea = 0;
bestX = 1; bestY = 1; bestW = 0; bestH = 0;

for r = 1:H
  heights = (heights + 1) .* double(mask(r, :));
  [area, left, right, hRect] = maxRectInHistogram(heights);
  if area > bestArea
      bestArea = area;
      bestX = left;
      bestW = right - left + 1;
      bestH = hRect;
      bestY = r - bestH + 1;
  end
end

if bestArea == 0
  error('No valid rectangle found in mask.');
end

bb = [bestX, bestY, bestW, bestH];
cropped = img_l_full(bb(2):(bb(2)+bb(4)-1), bb(1):(bb(1)+bb(3)-1), :);

end

% ---------------- Local function ----------------
function [bestArea, bestL, bestR, bestH] = maxRectInHistogram(h)
  h = [h, 0]; % sentinel to flush stack
  n = numel(h);

  stack = zeros(1, n);
  top = 0;

  bestArea = 0;
  bestL = 1; bestR = 0; bestH = 0;

  for i = 1:n
      while top > 0 && h(stack(top)) > h(i)
          height = h(stack(top));
          top = top - 1;

          if top == 0
              left = 1;
          else
              left = stack(top) + 1;
          end
          right = i - 1;

          area = height * (right - left + 1);
          if area > bestArea
              bestArea = area;
              bestL = left;
              bestR = right;
              bestH = height;
          end
      end

      top = top + 1;
      stack(top) = i;
  end
end