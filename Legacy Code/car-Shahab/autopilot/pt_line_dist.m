function d = pt_line_dist(a, b, x)
% Signed distance from point X to a line defined by points A and B.

d = ((b(2) - a(2)) * x(1) - (b(1) - a(1)) * x(2) + b(1) * a(2) - b(2) * a(1)) / vnorm(b - a);
