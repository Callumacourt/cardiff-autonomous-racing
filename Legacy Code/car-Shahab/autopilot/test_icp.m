rand('seed', 4);
A = rand(2, 5);
alpha = deg2rad(20);
R = [cos(alpha) -sin(alpha); sin(alpha) cos(alpha)];
T = [1.0; 3.0];
B = R * A + T + rand(size(A)) * 0.05;
B(:, 3) = []; % Remove some points

Ac = mean(A, 2);
An = subcol(A, Ac);
Bc = mean(B, 2);
Bn = subcol(B, Bc);

gamma = linspace(-pi/2, pi/2, 7); %gamma(end) = [];
min_err = 1e10; best_H = [];
tic
for g = 1:numel(gamma)
    rot = [cos(gamma(g)) -sin(gamma(g)); sin(gamma(g)) cos(gamma(g))];
    An_rot = rot * An;
    cost = zeros(size(A, 2), size(B, 2));
    for i = 1:size(A, 2)
        for j = 1:size(B, 2)
            %         if A(3, i) ~= B(3, j)
            %             cost(i, j) = 1000;
            %         else
            cost(i, j) = vnorm(An_rot(1:2, i) - Bn(1:2, j));
            %         end
        end
    end
    [H, err] = hungarian(cost);
    
    if err < min_err
        min_err = err
        rad2deg(gamma(g))
        best_H = H;
    end
end
toc
[row, col] = find(best_H);
edges = [row col]';
edge_cost = cost(best_H == 1);
edges(:, edge_cost >= 1000) = [];
edge_cost(edge_cost >= 1000) = [];

AA = A(:, edges(1, :));
BB = B(:, edges(2, :));
AAc = mean(AA, 2);
AAn = subcol(AA, AAc);
BBc = mean(BB, 2);
BBn = subcol(BB, BBc);

W = BBn * AAn';
[V, ~, Vt] = svd(W);
R_ = V * Vt
rad2deg(acos(R_(1)))
T_ = BBc - R_ * AAc

B_ = R_ * A + T_;
figure(1); clf;
hold on
plot(A(1, :), A(2, :), 'r.', 'MarkerSize', 32);
plot(B(1, :), B(2, :), 'b.', 'MarkerSize', 32);
plot(B_(1, :), B_(2, :), 'ro', 'MarkerSize', 16);
grid minor
hold off
