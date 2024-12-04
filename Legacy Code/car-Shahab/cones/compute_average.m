function [avg, E, X] = compute_average(fn, B, buf)

avg = zeros(size(buf), 'single');

last_fn = '';
N = size(B, 2);
X = zeros(numel(buf), N, 'single');
for i = 1:N
    if ~strcmpi(fn{i}, last_fn)
        im = imread(fn{i});
        last_fn = fn{i};
    end
    getwndbl_scale(buf, im, B(1, i), B(2, i), B(3, i), B(4, i));

    imwrite(buf ./ 255, sprintf('alignment/patches/%05d.png', i));
    X(:, i) = buf(:);
    avg = avg + buf;
    progress(i / N);
end
avg = avg ./ N;

E = 0;
for i = 1:size(X, 2)
    for j = i + 1:size(X, 2)
        E = E + sum(abs(X(:, i) - X(:, j)));
    end
end
E = E / (size(X, 1) * size(X, 2) * (size(X, 2) - 1) * 0.5);
% E = abs(subcol(X, avg(:)));
% E = mean(E(:));
