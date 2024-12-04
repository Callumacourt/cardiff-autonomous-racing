function E = compute_error(avg, fn, B, buf)

last_fn = '';
N = size(B, 2);
E = 0;
for i = 1:N
    if ~strcmpi(fn{i}, last_fn)
        im = imread(fn{i});
        last_fn = fn{i};
    end
    getwndbl_scale(buf, im, B(1, i), B(2, i), B(3, i), B(4, i));
    E = E + sum(abs(avg(:) - buf(:)));
    progress(i / N);
end
E = E ./ (N * numel(buf));
