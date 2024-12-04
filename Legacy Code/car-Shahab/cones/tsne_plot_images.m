function E = tsne_plot_images(X, im)

numDims = 2; pcaDims = min(32, size(X, 1)); perplexity = 50; theta = .5; alg = 'svd';
if size(X, 2) < 150, perplexity = round(size(X, 2) / 6); end
Y = fast_tsne(X', numDims, pcaDims, perplexity, theta, alg);
Y = Y';
[U, ~, Av] = kspca(Y);
Y = U * bsxfun(@minus, Y, Av);

range = diff(minmax(Y)');
w = 8192;
h = ceil(range(2) / range(1) * w);
[th, tw, ~] = size(im(:, :, 1));
E = zeros(h + th, w + tw);
Y(1, :) = Y(1, :) - min(Y(1, :));
Y(2, :) = Y(2, :) - min(Y(2, :));

C = round([(w - 1) / max(Y(1, :)) * Y(1, :) + 1; (h - 1) / max(Y(2, :)) * Y(2, :) + 1]);

for i = 1:size(C, 2)
    %     tn = imresize(im(:, :, i), [th tw]);
    tn = im(:, :, :, i);
    E(C(2, i):C(2, i)+th-1, C(1, i):C(1, i)+tw-1, :) = ...
        tn;
end
