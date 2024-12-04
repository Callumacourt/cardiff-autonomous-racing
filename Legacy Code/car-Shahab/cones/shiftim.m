function result = imshift(im, drow, dcol)

result = zeros(size(im), 'like', im);
[h, w, d] = size(im);

result(max(1, 1 + drow):min(h, h + drow), max(1, 1 + dcol):min(w, w + dcol), :) = ...
    im(max(1 - drow, 1):min(h, h - drow), max(1 - dcol, 1):min(w, w - dcol), :);
