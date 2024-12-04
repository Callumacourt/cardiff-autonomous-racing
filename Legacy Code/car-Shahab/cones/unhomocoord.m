function x = unhomocoord(H)

x = H(1:end-1, :) ./ repmat(H(end, :), 3, 1);
