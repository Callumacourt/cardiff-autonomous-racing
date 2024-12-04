if 0
im = imread('track_boundaries/track1.png');
im = im(:, :, 1);
D = bwdist(im);
T = D <= 15;
T = imresize(T, 0.5, 'nearest');
end