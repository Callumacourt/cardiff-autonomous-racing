function pix = im2pix(im)

c1 = im(:, :, 1); c1 = c1(:);
c2 = im(:, :, 2); c2 = c2(:);
c3 = im(:, :, 3); c3 = c3(:);
pix = [c1'; c2'; c3'];