function D = ccdist(cc)
% Pairwise distances between connected components

D = inf(cc.NumObjects);
for i = 1:size(D, 1)
    D(i, i) = 0;
    [row_i, col_i] = ind2sub(cc.ImageSize, cc.PixelIdxList{i});
    for j = i+1:size(D, 2)
        [row_j, col_j] = ind2sub(cc.ImageSize, cc.PixelIdxList{j});
        d = distance([row_i, col_i]', [row_j, col_j]');
        D(i, j) = min(d(:));
        D(j, i) = D(i, j);
    end
end

