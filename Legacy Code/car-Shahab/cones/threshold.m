function x = threshold(x, a)

t = sort(x(:));
x = x > t(round(numel(t) * a));