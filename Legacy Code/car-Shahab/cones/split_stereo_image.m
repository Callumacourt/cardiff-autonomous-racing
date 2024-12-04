function [L, R] = split_stereo_image(im)

[h, w, d] = size(im);
L = im(:, 1:w / 2, :);
R = im(:, w / 2 + 1:end, :);

