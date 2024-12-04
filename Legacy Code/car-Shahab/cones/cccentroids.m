function ctr = cccentroids(cc, im, threshold)

ctr = zeros(4, cc.NumObjects);
for i = 1:cc.NumObjects
    val = im(cc.PixelIdxList{i});
    den = sum(val);
    [row, col] = ind2sub(cc.ImageSize, cc.PixelIdxList{i});
    ctr(1, i) = sum(col .* val) / den;
    ctr(2, i) = sum(row .* val) / den;
    ctr(3, i) = sqrt(den / pi);
    ctr(4, i) = nnz(val > threshold);
end
