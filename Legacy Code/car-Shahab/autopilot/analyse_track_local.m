function [tri, edges_y, edges_b, cline, cline_i, centre, evec, V, xx, yy] = analyse_track_local(c)

[tri, edges_y, edges_b] = find_track_boundaries(c);

% Find cline
trans = [];
for i = 1:size(tri, 2)
    t = tri(:, i);
    for v = 0:2
        if c(3, t(v + 1)) ~= c(3, t(mod(v + 1, 3) + 1))
            edge = sort([t(v + 1); t(mod(v + 1, 3) + 1)]);
            if vnorm(c(1:2, edge(1)) - c(1:2, edge(2))) > MAX_EDGE, continue; end
            trans = [trans edge]; %#ok<AGROW>
        end
    end
end
trans = uniquerows(trans')';
cline = zeros(2, size(trans, 2));
for i = 1:size(cline, 2)
    cline(:, i) = 0.5 * (c(1:2, trans(1, i)) + c(1:2, trans(2, i)));
end

[evec, eval, centre] = kspca(cline);
proj = evec' * subcol(cline, centre);

p = fit_poly(proj);

x = linspace(-20, 20, 21);
cline_i_proj = [x; polyval(p, x)];
cline_i = addcol(evec * cline_i_proj, centre);


[xx, yy] = meshgrid(linspace(-10, 10, 51), linspace(0, 20, 51));
X = [xx(:) yy(:)]';
X0 = evec' * subcol(X, centre);
[D, V, Ds] = poly_dist(cline_i_proj, X0);

V = evec * V;
vn = vnorm(V);
V = [-V(2, :); V(1, :)];
V = V ./ vn;
V = V .* exp(-vn * 1.0);

% Global orientation
cyt = evec' * subcol(c(1:2, c(3, :) == 0), centre);
[Dy, Vy, Dsy] = poly_dist(cline_i_proj, cyt);

Dsy = mean(Dsy);
neg = sign(Ds) * sign(Dsy) < 0;
V(:, neg) = -V(:, neg);
