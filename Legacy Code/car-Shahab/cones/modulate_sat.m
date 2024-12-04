function im = modulate_sat(im, P)

P = P - min(P(:));
P = P / max(P(:));
hsv = rgb2hsv(im);

im = hsv2rgb(cat(3, hsv(:, :, 1), P .* hsv(:, :, 2), hsv(:, :, 3)));