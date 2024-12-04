function X_resized = resize_patches(X, h0, w0, h1, w1, colour)

fprintf('Resizing negative examples to %dx%d...', h1, w1);

if colour
    X_resized = zeros(h1 * w1 * 3, size(X, 2), 'single');
else
    X_resized = zeros(h1 * w1, size(X, 2), 'single');
end
for i = 1:size(X, 2)
    if colour
        t = imresize(reshape(X(:, i), h0, w0, 3), [h1 w1], ...
            'bilinear', 'antialiasing', false);
    else
        x = 255 * rgb2gray(reshape(X(:, i), h0, w0, 3) / 255);
        t = imresize(x, [h1 w1], ...
            'bilinear', 'antialiasing', false);
    end
    X_resized(:, i) = t(:);
end
fprintf('done\n');
