function idx = quantize_pix(pix, ctr)

D = distance(ctr, pix);
[~, idx] = min(D);