track_fn = '../track3.mat';
track = load(track_fn);
inner = track.inner;
outer = track.outer;
dist = track.dist;

genomes = list_files('state/best_genome.*');

for gen = 1:1:numel(genomes)
    outfn = sprintf('traj3/%04d.png', gen);
    if exist(outfn, 'file')
        continue
    end
    outfn
% tic
fig(1); clf;
sc(dist * 0);
hold on
% I = sc(cat(3, track.fx, track.fy), 'flow');
% sc(1 - I);
% sc(dist, jet);
plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b', 'LineWidth', 1);
plot(inner(1, :), inner(2, :), 'b.', 'MarkerSize', 16);
plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'y', 'LineWidth', 1);
plot(outer(1, :), outer(2, :), 'y.', 'MarkerSize', 16);

N = 100;
for i = 1:N
%     tic
    X = get_trajectory(genomes{gen}, track_fn);
%     toc
    plot(X(1, :), X(2, :), 'w');
    plot(X(1, end), X(2, end), 'r+', 'MarkerSize', 10);
    drawnow
    xlim([1 256])
    ylim([1 256])
end
hold off
export_fig(outfn, '-nocrop')
% toc
end

function X = get_trajectory(genome, track)
command = ['./trajectory.py --agent ' genome ' --track ' track];
[~, cmdout] = system(command);
lines = splitlines(cmdout);
lines = lines(2:end-1);

X = zeros(3, numel(lines));
for i = 1:numel(lines)
    x = textscan(lines{i}, '%f');
    X(:, i) = x{1};
end
end