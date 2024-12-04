if 0
    fn = list_files('../../car_data/cones/amz/every10/*.png');
    im = imread(fn{1});
    [h, w, d] = size(im);
    
    sz = 30;
    top = 1:sz:h;
    left = 1:sz:w;
    X = zeros(d * sz * sz, numel(top) * numel(left) * numel(fn));
    pos = 1;
    for i = 1:numel(fn)
        im = imread(fn{i});
        for row = 1:numel(top)
            for col = 1:numel(left)
                patch = im(top(row):top(row)+sz-1, left(col):left(col)+sz-1, :);
                X(:, pos) = patch(:);
                pos = pos + 1;
            end
        end
    end
    [evec, eval, avg] = kspca(X);
    quality = 0.95;
    keep = find(cumsum(eval) / sum(eval) > quality, 1);
    basis = evec(:, 1:keep);
    
    proj = basis' * subcol(X, avg);
    Xrec = addcol(basis * proj, avg);
end
pos = 1;
for i = 1:numel(fn)
    imrec = zeros(size(im));
    for row = 1:numel(top)
        for col = 1:numel(left)
            imrec(top(row):top(row)+sz-1, left(col):left(col)+sz-1, :) = reshape(Xrec(:, pos), sz, sz, d);
            pos = pos + 1;
        end
    end
    i
    figure(1);
    sc(imrec);
    drawnow;
end
