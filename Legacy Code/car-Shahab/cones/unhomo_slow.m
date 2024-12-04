function X = unhomo(H)

rows = size(H, 1);
X = H(1:rows - 1, :) ./ repmat(H(rows, :), rows - 1, 1);
