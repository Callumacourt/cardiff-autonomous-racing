function result = matlab2opencv3(im)

[h, w, d] = size(im);
r = im(:, :, 1)'; r = r(:);
g = im(:, :, 2)'; g = g(:);
b = im(:, :, 3)'; b = b(:);
% a = zeros(size(b), 'like', im);

result = [r g b]';
result = reshape(result(:), [h, w, 3]);

