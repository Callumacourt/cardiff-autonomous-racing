function pix = patches2pixels(X)
dim = size(X, 1) / 3;
r = X(1:dim, :);
g = X(dim + 1:dim * 2, :);
b = X(dim * 2 + 1:end, :);
pix = [r(:) g(:) b(:)]';
end