function P = pot_poly(x, poly, Q)

if nargin < 3
    Q = ones(1, size(poly, 2));
end
P = zeros(1, size(x, 2));
for i = 1:size(poly, 2)
    q = Q(i);%(Q(i) + Q(j)) * 0.5;
    p = pot_segment(x, poly(1:2, i), poly(3:4, i), q, q);
    P = P + p;
end
