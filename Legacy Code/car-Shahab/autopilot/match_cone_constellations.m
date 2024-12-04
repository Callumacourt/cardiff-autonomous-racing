function [R, T, edges] = match_cone_constellations(cc, cc_prev)

MAX_DIST = 2.0;
[theta, rho] = cart2pol(cc(1, :), cc(2, :));
[theta_prev, rho_prev] = cart2pol(cc_prev(1, :), cc_prev(2, :));

cc_pol = [theta; rho]; cc_pol_prev = [theta_prev; rho_prev];
% Compute cost matrix for tentative assignment
cost = zeros(size(cc_pol, 2), size(cc_pol_prev, 2));
for i = 1:size(cc_pol, 2)
    for j = 1:size(cc_pol_prev, 2)
        d = vnorm(cc_pol(1:2, i) - cc_pol_prev(1:2, j));
        if cc(3, i) ~= cc_prev(3, j) || d > MAX_DIST
            cost(i, j) = 1000;
        else
            cost(i, j) = d;
        end
    end
end
[H, ~] = hungarian(cost);
[row, col] = find(H);
edges = [row col]';
edge_cost = cost(H == 1);
edges(:, edge_cost >= 1000) = [];

a = cc(1:2, edges(1, :));
a_prev = cc_prev(1:2, edges(2, :));
a_ctr = mean(a, 2);
a_prev_ctr = mean(a_prev, 2);
ac = subcol(a, a_ctr);
ac_prev = subcol(a_prev, a_prev_ctr);

[V, ~, Vt] = svd(ac_prev * ac');
R = V * Vt;
T = a_prev_ctr - R * a_ctr;
