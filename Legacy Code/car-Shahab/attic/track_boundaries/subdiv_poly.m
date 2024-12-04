function [spoly, sQ] = subdiv_poly(poly, delta, Q)


spoly = [];
sQ = [];
for i = 1:size(poly, 2)
    j = mod(i, size(poly, 2)) + 1;
    v1 = poly(:, i);
    v2 = poly(:, j);
    len = norm(v2 - v1);
    x = linspace(v1(1), v2(1), len / delta);
    y = linspace(v1(2), v2(2), len / delta);
    spoly = [spoly [x(1:end-1); y(1:end-1)]]; %#ok<*AGROW>
    if nargin > 2
        q = linspace(Q(i), Q(j), len / delta);
        sQ = [sQ q(1:end-1)];
    end
end

