function im = imtriplot(im, tri, x, colour, alpha)

X0 = [];
X1 = [];
V = [];

for i = 1:size(tri, 1)
    x0 = x(:, tri(i, :));
    x1 = [x0(:, 2:end) x0(:, 1)];
    X0 = [X0 x0];
    X1 = [X1 x1];
    
    v0 = tri(i, :);
    v1 = [tri(i, 2:end) tri(i, 1)];
    V = [V sort([v0; v1])];
end
[~, keep, ~] = unique(V', 'rows');
draw_line(im, X0(:, keep), X1(:, keep), colour, alpha);
