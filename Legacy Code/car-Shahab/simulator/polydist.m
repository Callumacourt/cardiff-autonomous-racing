function P = polydist(poly, XX)

P = inf(1, size(XX, 2));
for i = 1:size(poly, 2)
    P = min(P, psdist(poly(1:2, i), poly(3:4, i), XX));
end
