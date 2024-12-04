function [tri, edges_y, edges_b] = find_track_boundaries(c)

MAX_EDGE = 7.5;

tri = delaunay(c(1, :), c(2, :))';

% Remove triangle whose vertices are all of the same colour
col = c(3, :);
col_sum = sum(col(tri));
tri(:, col_sum == 0 | col_sum == 3) = [];

% Find track boundaries
edges_b = [];
edges_y = [];
for i = 1:size(tri, 2)
    t = tri(:, i);
    for v = 0:2
        if c(3, t(v + 1)) ~= c(3, t(mod(v + 1, 3) + 1)) && ...
                c(3, t(v + 1)) ~= c(3, t(mod(v + 2, 3) + 1)) && ...
                c(3, t(mod(v + 1, 3) + 1)) == c(3, t(mod(v + 2, 3) + 1))
            edge = sort([t(mod(v + 1, 3) + 1); t(mod(v + 2, 3) + 1)]);
            if vnorm(c(1:2, edge(1)) - c(1:2, edge(2))) > MAX_EDGE, continue; end
            if c(3, t(v + 1)) == 0
                edges_b = [edges_b edge];  %#ok<AGROW>
            else
                edges_y = [edges_y edge];  %#ok<AGROW>
            end
        end
    end
end
