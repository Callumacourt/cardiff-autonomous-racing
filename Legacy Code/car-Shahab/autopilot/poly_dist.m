function [D, V, Ds] = poly_dist(poly, X)

V = zeros(2, size(X, 2));
D = inf(1, size(X, 2));
Ds = inf(1, size(X, 2));
for i = 1:size(poly, 2) - 1
    v0 = poly(:, i);
    v1 = poly(:, i + 1);
    [d, v] = psdist(v0, v1, X);
    
    v1v0 = v1 - v0;
    n = [-v1v0(2); v1v0(1)];
    ds = d .* sign(dot(v, repmat(n, 1, size(v, 2))));
    
    V(:, d < D) = v(:, d < D);
    Ds(:, d < D) = ds(:, d < D);
    D = min(d, D);
end
