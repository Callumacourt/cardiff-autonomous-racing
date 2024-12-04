cones = load('cones_4.txt');
cones = cones(:, 1:2)' * 0.01;
cones = [cones [-157.55 -154.2; -251.45 -250.35]];

fig(1); clf;

axis equal
tri = delaunay(cones(1, :), cones(2, :));
edges = [];
tri_inner = [];
MAX_EDGE = 5.8;
for i = 1:size(tri, 1)
    e1 = sort([tri(i, 1); tri(i, 2)]);
    e2 = sort([tri(i, 2); tri(i, 3)]);
    e3 = sort([tri(i, 3); tri(i, 1)]);
    if vnorm(cones(:, e1(1)) - cones(:, e1(2))) < MAX_EDGE && ...
            vnorm(cones(:, e2(1)) - cones(:, e2(2))) < MAX_EDGE && ...
            vnorm(cones(:, e3(1)) - cones(:, e3(2))) < MAX_EDGE
        tri_inner = [tri_inner; tri(i, :)];
        edges = [edges e1 e2 e3];
    end
end
edge_len = vnorm(cones(:, edges(1, :)) - cones(:, edges(2, :)));
edges(:, edge_len > MAX_EDGE) = [];
% edges = sortrows(edges')';
edges_outer = [];
for i = 1:size(edges, 2)
    if nnz(all(edges(:, i) == edges)) == 1
        edges_outer = [edges_outer edges(:, i)];
    end
end

pt_inner = edges_outer(1, 10);
A = zeros(max(edges_outer(:)));
for i = 1:size(edges_outer, 2)
    A(edges_outer(1, i), edges_outer(2, i)) = 1;
    A(edges_outer(2, i), edges_outer(1, i)) = 1;
end
G = graph(A);
cc = conncomp(G);

yellow = cones(:, cc == cc(pt_inner));
blue = cones(:, cc ~= cc(pt_inner));


hold on
% triplot(tri_inner, cones(1, :), cones(2, :));
% for i = 1:size(edges_outer, 2)
%     plot(cones(1, edges_outer(:, i)), cones(2, edges_outer(:, i)), 'r');
% end
plot(yellow(1, :), yellow(2, :), 'y.', 'MarkerSize', 16);
plot(blue(1, :), blue(2, :), 'b.', 'MarkerSize', 16);
% plot(cones(1, edges_outer(1, 10)), cones(2, edges_outer(1, 10)), 'go', 'MarkerSize', 16);

hold off


all_cones = [[ones(1, size(yellow, 2)); yellow] [ones(1, size(yellow, 2)) + 1; blue]]';
ctr = mean(all_cones(:, 2:3));
all_cones = [all_cones(:, 1) all_cones(:, 2:3) - ctr];
writematrix(all_cones, 'cones_4_labelled.txt');
