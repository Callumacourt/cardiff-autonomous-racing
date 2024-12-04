function E = imscatter(Y, im)

range = diff(minmax(Y)');
w = 8192;
h = ceil(range(2) / range(1) * w);
[th, tw, ~] = size(im(:, :, 1));
E = zeros(h + th, w + tw, size(im, 3));
Y(1, :) = Y(1, :) - min(Y(1, :));
Y(2, :) = Y(2, :) - min(Y(2, :));

C = round([(w - 1) / max(Y(1, :)) * Y(1, :) + 1; (h - 1) / max(Y(2, :)) * Y(2, :) + 1]);

for i = 1:size(C, 2)
    %     tn = imresize(im(:, :, i), [th tw]);
    tn = im(:, :, :, i);
    E(C(2, i):C(2, i)+th-1, C(1, i):C(1, i)+tw-1, :) = ...
        tn;
end
