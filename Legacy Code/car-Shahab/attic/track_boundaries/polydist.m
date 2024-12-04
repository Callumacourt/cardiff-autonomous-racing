function P = polydist(poly, XX)

P = inf(size(XX));
for i = 1:size(poly, 2)
    P = min(P, psdist(poly(1:2, i), poly(3:4, i), XX));
end
