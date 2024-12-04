data = fileread('cones_recorded.txt');
data = textscan(data, '%s', 'Delimiter', '\n'); data = data{1};
data(cellfun(@isempty, data)) = [];
N = numel(data);
cones = cell(N, 1);
for i = 1:N
    cones{i} = cell2mat(textscan(data{i}, '%f %f %f'));
end
whitebg('black');

car = [0; 0];
car_fwd = [1; 0];
car_hdg = eye(2);
dist = 0;


c_hist = zeros(3, 0);
c_prev = [];
fig(2); clf;
grid minor

CAR = [];
CAR_FWD = [];
for f = 100:N
    c = cones{f}; c = c(:, [2 3 1])';
    
    if isempty(c_prev)
        c_prev = c;
    end
    
    [R, T, edges] = match_cone_constellations(c, c_prev);
    
    car_hdg = R * car_hdg; % TODO: Is this order correct?
    car = car + car_hdg * T;
    
    dist = dist + vnorm(T);
    CAR = [CAR car];
    
    dist = dist + vnorm(T);
    
    % Record history
    [R_inv, T_inv] = invert_rt(R, T);
    c_hist = [[R_inv * c_hist(1:2, :) + T_inv; c_hist(3, :)] c];
    c_hist(:, c_hist(2, :) < -5) = []; % Remove points behind us
    % Cluster nearby points in history
    %     c = [cluster_cones(c_hist(:, c_hist(3, :) == 0)) cluster_cones(c_hist(:, c_hist(3, :) == 1))];
    c = cluster_cones(c_hist);
    
    
    [tri, edges_y, edges_b, cline, cline_i, centre, evec, V, xx, yy] = analyse_track_local(c);
    
    
    
    
    
    fig(1); clf;
    axis([-15 15 -5 25]);
    hold on
    
    
    Vx = reshape(V(1, :), size(xx));
    Vy = reshape(V(2, :), size(xx));
    quiver(xx, yy, Vx, Vy, 'Color', [0.1 0.5 0.0], 'LineWidth', 2);
    
    triplot(tri', c(1, :), c(2, :), 'w:');
    
    for i = 1:size(edges_y, 2)
        line([c(1, edges_y(1, i)) c(1, edges_y(2, i))], [c(2, edges_y(1, i)) c(2, edges_y(2, i))], 'Color', 'y', 'LineWidth', 2);
    end
    for i = 1:size(edges_b, 2)
        line([c(1, edges_b(1, i)) c(1, edges_b(2, i))], [c(2, edges_b(1, i)) c(2, edges_b(2, i))], 'Color', 'b', 'LineWidth', 2);
    end
    
    plot(c(1, c(3, :) == 0), c(2, c(3, :) == 0), 'y.', 'MarkerSize', 20);
    plot(c(1, c(3, :) == 1), c(2, c(3, :) == 1), 'b.', 'MarkerSize', 20);
    %     for i = 1:size(c, 2)
    %         text(c(1, i) + 0.2, c(2, i) + 0.2, num2str(i));
    %     end
    
    % Centreline
    plot(cline_i(1, :), cline_i(2, :), 'w', 'LineWidth', 2);
    plot(cline(1, :), cline(2, :), 'wo', 'MarkerSize', 5);
    % Prinipal component
    len = 7;
    x0 = centre + len * evec(:, 1);
    x1 = centre - len * evec(:, 1);
    line([x0(1) x1(1)], [x0(2) x1(2)], 'Color', 'r', 'LineStyle', '--');
    %     for i = 1:size(c, 2)
    %         text(c(1, i) + 0.2, c(2, i) + 0.2, num2str(i));
    %     end
    
    c_prev = c;
    hold off
    grid minor
    
    fig(2);
    axis([-20 40 -60 110]);
    hold on
    plot(car(1), car(2), 'g.');
    hold off
    drawnow;
    %     pause
    
    
    %     export_fig(sprintf('out/%06d.png', f), '-png');
    
end
