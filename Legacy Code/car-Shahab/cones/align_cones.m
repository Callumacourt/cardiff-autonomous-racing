if 1
    opt.labels = [1];
    fprintf('Loading annotations...');
    [imfn, bb] = load_annotated_cones('augmented', false);
    Nbb = sum(cellfun(@numel, bb) / 5);
    fprintf('done\n');
    
    H = []; W = [];
    B = zeros(4, Nbb);
    fn = cell(Nbb, 1);
    count = 1;
    for i = 1:numel(bb)
        if isempty(bb{i}), continue; end
        for j = 1:size(bb{i}, 1)
            if ~ismember(bb{i}(j, 1), opt.labels), continue; end
            H = [H; bb{i}(j, 5)];
            W = [W; bb{i}(j, 4)];
            B(:, count) = bb{i}(j, 2:end);
            fn{count} = imfn{i};
            count = count + 1;
        end
    end
    B(:, count:end) = [];
    fn(count:end) = [];
end

ratio = mean(W) / mean(H);
bufw = ceil(mean(W));
bufh = ceil(mean(H));

mask = imresize(im2double(imread('alignment_mask.png')), ...
    [bufh bufw], 'bilinear', 'antialiasing', false);
mask = single(mask);

buf = zeros(bufh, bufw, 3, 'single');

% B = B(:, 1:100);

N = size(B, 2);
for iter = 1:100
    fprintf('ITERATION %d\n', iter);
    fprintf('Computing average...');
    [avg, E, X] = compute_average(fn, B, buf);
    imwrite(avg ./ 255, sprintf('alignment/avg%05d.png', iter));
    %     E = compute_error(avg, fn, B, buf);
    fprintf('Error: %.5f\n', E);
    
    fprintf('Aligning to average...');
    last_fn = '';
    I = zeros(size(B));
    tic
    for i = 1:N
        if ~strcmpi(fn{i}, last_fn)
            im = imread(fn{i});
            last_fn = fn{i};
        end
        improved = align_pairwise(avg, im, B(:, i), X, mask, buf);
        I(:, i) = improved(:);
        progress(i / N);
    end
    toc
    I = enforce_cm(enforce_area(I, B), B);
    B = I;
    save(sprintf('alignment/B%05d.mat', iter), 'B');
    fprintf('\n');
end



