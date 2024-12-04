rng('default'); rng(1);

[inner, outer] = im2cones('data/track2.png');
inner = inner(:, 1:2:end) * 3;
outer = outer(:, 1:2:end) * 3;

track_width = 6;
cone_dist = 8;
h = 128; w = 128; d = 24;
scale = h / 80;

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

kdo = KDTreeSearcher(outer');
% figure(2); clf;
% hold on
% plot(inner(1, :), inner(2, :), 'bo');
% plot(outer(1, :), outer(2, :), 'go');
% axis ij
% hold off

kdi = KDTreeSearcher(inner');
kdo = KDTreeSearcher(outer');

seg_inner = [inner; [inner(:, 2:end) inner(:, 1)]];
seg_outer = [outer; [outer(:, 2:end) outer(:, 1)]];

% Pi = polydist(seg_inner, X');
Pi = inf(1, size(X', 2));
for i = 1:size(seg_inner, 2)
%     if vnorm(seg_inner(1:2, i) - seg_inner(3:4, i)) > cone_dist, continue; end
    Pi = min(Pi, psdist(seg_inner(1:2, i), seg_inner(3:4, i), X'));
end
Po = inf(1, size(X', 2));
for i = 1:size(seg_outer, 2)
%     if vnorm(seg_outer(1:2, i) - seg_outer(3:4, i)) > cone_dist, continue; end
    Po = min(Po, psdist(seg_outer(1:2, i), seg_outer(3:4, i), X'));
end

probio = normpdf(Pi, track_width, track_width / 3);
probi = normpdf(Pi, 0, track_width / 3);

proboi = normpdf(Po, track_width, track_width / 3);
probo = normpdf(Po, 0, track_width / 3);

figure(4);
sc(reshape((probi + probio) .* (probo + proboi), h, w))
plot_track(inner, outer, scale, cone_dist);


