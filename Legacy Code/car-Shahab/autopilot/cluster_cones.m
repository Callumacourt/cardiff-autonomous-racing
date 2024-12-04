function CC = cluster_cones(C)

MAX_CLUSTER_DIST = 0.5;
D = distance(C, C);
A = D < MAX_CLUSTER_DIST;
G = graph(A);
[conn, cnt] = conncomp(G);
Ncc = max(conn);
CC = zeros(3, Ncc);
for i = 1:Ncc
    CC(1:2, i) = mean(C(1:2, conn == i), 2);
    CC(3,  i) = mode(C(3, conn == i));
end

