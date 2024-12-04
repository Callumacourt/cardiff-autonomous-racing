function im = pix2im(pix, h, w)

im = cat(3, reshape(pix(1, :), h, w), reshape(pix(2, :), h, w), reshape(pix(3, :), h, w));