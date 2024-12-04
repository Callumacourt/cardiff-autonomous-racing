
V = [];
for evec = 1:8
    sigma = std(proj_original(evec, :));
    std(proj_original(evec, :))
    n = 9;
    param = linspace(-3, 3, n) * sigma;
    c = zeros(size(proj_original, 1), n);
    c(evec, :) = param;

    unproj = addcol(am.B(:, 1:am.keep) * c, am.avg);
    V = [V; (reshape(permute(reshape(unproj, am.ch, am.cw, 3, n), [1 2 4 3]), am.ch, am.cw * n, 3))];
end
figure(3); clf;
sc(V);
c
