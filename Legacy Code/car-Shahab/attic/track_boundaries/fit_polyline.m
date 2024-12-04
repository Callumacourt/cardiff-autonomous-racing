function edges = fit_polyline(X, objfun, varargin)

opt.method = 'tsp';
opt.iter = 30000;
opt.max_dist = 10000;
opt = parseargs(opt, varargin{:});

switch lower(opt.method)
    case 'tsp'
        D = distance(X, X);
%         D(D > opt.max_dist) = 10000;
        result = tsp_ga_custom(objfun, 'xy', X', 'showProg', true, 'showResult', false, ...
            'numIter', opt.iter, 'dmat', D);
        tour = result.optRoute;
        % [tour, len] = tsp(I');
        edges = [tour; [tour(2:end) tour(1)]]';
    case 'mst'
        G = graph(distance(X, X));
        [T, ~] = minspantree(G);
        edges = table2array(T.Edges);  
end



x1 = X(:, edges(:, 1));
x2 = X(:, edges(:, 2));
dist = vnorm(x1 - x2);
remove = dist > opt.max_dist;
edges(remove, :) = [];
