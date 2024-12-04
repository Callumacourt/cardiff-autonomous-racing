function im = im_homography(im, H)

im = im2double(im);
[h, w, ~] = size(im);
[xx, yy] = meshgrid(1:w, 1:h);

c = [xx(:) yy(:)]';

% cn = inv(H) * c;
cn = homography_transform(c, H);
c1 = interp2(im(:, :, 1), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
c2 = interp2(im(:, :, 2), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
c3 = interp2(im(:, :, 3), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
im = cat(3, c1, c2, c3);