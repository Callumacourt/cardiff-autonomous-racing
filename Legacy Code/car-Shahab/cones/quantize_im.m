function im = quantize_im(im, ctr)

[h, w, d] = size(im);
pix = im2pix(im);
quant = quantize_pix(pix, ctr);
im = pix2im(ctr(:, quant), h, w);