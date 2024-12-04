function H = col_histogram(pix)

H = zeros(16, 16, 16);
pix = bitshift(pix, -4);
for i = 1:size(pix, 2)
    H(pix(1, i) + 1, pix(2, i) + 1, pix(3, i) + 1) = H(pix(1, i) + 1, pix(2, i) + 1, pix(3, i) + 1) + 1;
end