rng('default'); rng(1);

[inner, outer] = im2cones('data/track2.png');
inner = inner(:, 1:2:end) * 3;
outer = outer(:, 1:2:end) * 3;

track_width = 6;
cone_dist = 8;

% figure(1); clf;
% hold on
% plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b');
% plot(inner(1, :), inner(2, :), 'bo');
% plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'g');
% plot(outer(1, :), outer(2, :), 'go');
% axis ij
% hold off


% Decimate
keep = 0.3;
idx = randperm(size(inner, 2));
inner(:, idx(1:randi(round(size(inner, 2) * keep)))) = [];
idx = randperm(size(outer, 2));
outer(:, idx(1:randi(round(size(outer, 2) * keep)))) = [];

% figure(2); clf;
% hold on
% plot(inner(1, :), inner(2, :), 'bo');
% plot(outer(1, :), outer(2, :), 'go');
% axis ij
% hold off

kdi = KDTreeSearcher(inner');
kdo = KDTreeSearcher(outer');


h = 128; w = 128; d = 24;

Di = zeros(h, w);
Do = zeros(h, w);
[xx yy] = meshgrid(linspace(0, 80, w), linspace(0, 80, h));
scale = h / 80;

X = [xx(:) yy(:)];
[idxi, di] = knnsearch(inner', X, 'K', 1);
[idxo, do] = knnsearch(outer', X, 'K', 1);
Di = reshape(mean(di, 2), h, w);
Do = reshape(mean(do, 2), h, w);
% Di = reshape(min(di, [], 2), h, w);
% Do = reshape(min(do, [], 2), h, w);
% figure(4); sc(cat(3, Di, Do, zeros(size(Di))));
% figure(4); sc(abs(Di - Do) < 1);
% plot_track(inner, outer, scale, cone_dist);


N = h * w;
segclass = zeros(1, N);
mind = min(Di(:), Do(:));

indiv = zeros(2, numel(Di));
indiv(2, mind > track_width) = 10;
indiv(2, mind <= track_width) = 0;
indiv(1, mind > track_width) = 0;
indiv(1, mind <= track_width) = 1;
% indiv(1, Di(:) > track_width | Do(:) > track_width) = 0;

% indiv(2, Di(:) < track_width & Do(:) < track_width) = 0;
% indiv(2, ~(Di(:) < track_width & Do(:) < track_width)) = 1;
% indiv(1, Di(:) < track_width & Do(:) < track_width) = 1;
% indiv(1, ~(Di(:) < track_width & Do(:) < track_width)) = 0;
if 1
    pairwise = sparse(N, N);
    
    smoothness = 0.1;
    for row = 0:h-1
        for col = 0:w-1
            pixel = 1 + row*w + col;
            if row+1 < h, pairwise(pixel, 1+col+(row+1)*w) = smoothness; end
            if row-1 >= 0, pairwise(pixel, 1+col+(row-1)*w) = smoothness; end
            if col+1 < w, pairwise(pixel, 1+(col+1)+row*w) = smoothness; end
            if col-1 >= 0, pairwise(pixel, 1+(col-1)+row*w) = smoothness; end
        end
    end
end

superpe = sparse(N, N);
seg_outer = [outer; [outer(:, 2:end) outer(:, 1)]];
for i = 1:size(seg_outer, 2)
    a = seg_outer(1:2, i);
    b = seg_outer(3:4, i);
    if vnorm(b - a) > cone_dist, continue; end
    D = psdist(a, b, X');
    idx = find(D < track_width / 2);
    ab = b - a;
    ab = ab ./ vnorm(ab);
    ax = X(idx, :)' - a;
    ax = ax ./ vnorm(ax);
    c = sign(cross([repmat(ab, 1, size(ax, 2)); zeros(1, size(ax, 2))], [ax; zeros(1, size(ax, 2))]));
    c = c(3, :);
    
    for j = 1:numel(idx)
        for k = j+1:numel(idx)
            if k == j, continue; end
            if c(j) * c(k) < 0
                superpe(idx(j), idx(k)) = 1;
                superpe(idx(k), idx(j)) = 1;
            end
        end
    end
end

seg_inner = [inner; [inner(:, 2:end) inner(:, 1)]];
for i = 1:size(seg_inner, 2)
    a = seg_inner(1:2, i);
    b = seg_inner(3:4, i);
    if vnorm(b - a) > cone_dist, continue; end

    D = psdist(a, b, X');
    idx = find(D < track_width / 2);
    ab = b - a;
    ab = ab ./ vnorm(ab);
    ax = X(idx, :)' - a;
    ax = ax ./ vnorm(ax);
    c = sign(cross([repmat(ab, 1, size(ax, 2)); zeros(1, size(ax, 2))], [ax; zeros(1, size(ax, 2))]));
    c = c(3, :);
    
    for j = 1:numel(idx)
        for k = j+1:numel(idx)
            if k == j, continue; end
            if c(j) * c(k) < 0
                superpe(idx(j), idx(k)) = 1;
                superpe(idx(k), idx(j)) = 1;
            end
        end
    end
end


label_cost = [0.0 1; 1 0.0];
tic
% [labels E E_after] = GCMex(segclass, single(indiv), pairwise, single(label_cost), 0);
energy.UE = indiv;
energy.subPE = pairwise;
energy.superPE = superpe;
energy.constTerm = 0;

[labels E iter] = LSA_TR(energy);

toc

L = reshape(labels, h, w);
figure(5); sc(L);

plot_track(inner, outer, scale, cone_dist);
