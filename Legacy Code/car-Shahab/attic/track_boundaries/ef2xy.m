function [x, y] = ef2xy(X0, Y0, a, b, c, d, t)

n = [1:numel(a)]';
x = X0 + a' * cos(n .* t) + b' * sin(n .* t);
y = Y0 + c' * cos(n .* t) + d' * sin(n .* t);