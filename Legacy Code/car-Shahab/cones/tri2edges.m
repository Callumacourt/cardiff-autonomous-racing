function edges = tri2edges(tri)

V = [];

for i = 1:size(tri, 1)
    v0 = tri(i, :);
    v1 = [tri(i, 2:end) tri(i, 1)];
    V = [V sort([v0; v1])];
end
[edges, ~, ~] = unique(V', 'rows');
edges = edges';
