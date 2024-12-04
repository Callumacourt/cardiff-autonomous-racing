function plot_poly(edges, points, varargin)

for i = 1:size(edges, 1)
    plot([points(1, edges(i, 1)) points(1, edges(i, 2))], ...
        [points(2, edges(i, 1)) points(2, edges(i, 2))], varargin{:});
end