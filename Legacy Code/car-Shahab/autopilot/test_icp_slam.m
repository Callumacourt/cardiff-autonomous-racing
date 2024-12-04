data = fileread('cones_recorded.txt');
data = textscan(data, '%s', 'Delimiter', '\n'); data = data{1};
data(cellfun(@isempty, data)) = [];
N = numel(data);
cones = cell(N, 1);
for i = 1:N
    cones{i} = cell2mat(textscan(data{i}, '%f %f %f'));
end
whitebg('black');

figure(1); clf;



c_prev = [];

car = [0; 0];
car_hdg = eye(2);

figure(2); clf;
axis([-100 100 -50 150]);
grid minor

dist = 0;
C = zeros(3, 0);
cw_hdl_y = [];
for f = 1:1:N
    c = cones{f}; c = c(:, [2 3 1])';
    cy = c(1:2, c(3, :) == 0);
    cb = c(1:2, c(3, :) == 1);
    
    if isempty(c_prev)
        c_prev = c;
        continue;
    end
    
    cc = c;
    cc_prev = c_prev;
    
    % TODO: pre-rotate using the R from previous iteration?
    % TODO: doing this in polar coordinates! DONE
    % TODO: Incorporate inertial measurements and car model
    
    [R, T, edges] = match_cone_constellations(cc, cc_prev);
    % Transform to bring to correspondence
    c_t = [R * c(1:2, :) + T; c(3, :)];
    [R_inv, T_inv] = invert_rt(R, T);
    c_prev_t = [R_inv * c_prev(1:2, :) + T_inv; c_prev(3, :)];
        
    % Record history
    C = [[R_inv * C(1:2, :) + T_inv; C(3, :)] c];
    C(:, C(2, :) < -5) = []; % Remove points behind us    
    % Cluster nearby points in history
    CC = cluster_cones(C);

    % Ingegrate car state
    % TODO: Better way to integrate?
    new_car_hdg = R * car_hdg;
    new_car = car + car_hdg * T;
    dist = dist + vnorm(T);
    car_hdg = new_car_hdg;
    car = new_car;
    CW = car_hdg * C(1:2, :) + car; % Before of after integration?
  
    
    %
    % Plot results
    %
    
    fig(1);
    clf
    axis([-10 10 0 25]);
    hold on
    plot(cy(1, :), cy(2, :), 'y.', 'MarkerSize', 20);
    plot(cb(1, :), cb(2, :), 'b.', 'MarkerSize', 20);
    for i = 1:size(c, 2)
        text(c(1, i) + 0.2, c(2, i) + 0.2, num2str(i));
    end
    
    plot(c_prev(1, c_prev(3, :) == 0), c_prev(2, c_prev(3, :) == 0), 'y+', 'MarkerSize', 10);
    plot(c_prev(1, c_prev(3, :) == 1), c_prev(2, c_prev(3, :) == 1), 'b+', 'MarkerSize', 10);
    for i = 1:size(c_prev, 2)
        text(c_prev(1, i) + 0.2, c_prev(2, i) + 0.2, num2str(i));
    end
    
    plot(c_t(1, c_t(3, :) == 0), c_t(2, c_t(3, :) == 0), 'yo', 'MarkerSize', 10);
    plot(c_t(1, c_t(3, :) == 1), c_t(2, c_t(3, :) == 1), 'bo', 'MarkerSize', 10);
    plot(c_prev_t(1, c_prev_t(3, :) == 0), c_prev_t(2, c_prev_t(3, :) == 0), 'ys', 'MarkerSize', 10);
    plot(c_prev_t(1, c_prev_t(3, :) == 1), c_prev_t(2, c_prev_t(3, :) == 1), 'bs', 'MarkerSize', 10);

    %     plot(C(1, C(3, :) == 0), C(2, C(3, :) == 0), 'y.', 'MarkerSize', 1);
    %     plot(C(1, C(3, :) == 1), C(2, C(3, :) == 1), 'b.', 'MarkerSize', 1);
    plot(CC(1, CC(3, :) == 0), CC(2, CC(3, :) == 0), 'yd', 'MarkerSize', 4);
    plot(CC(1, CC(3, :) == 1), CC(2, CC(3, :) == 1), 'bd', 'MarkerSize', 4);
    
    % Draw matches
    for i = 1:size(edges, 2)
        line([c(1, edges(1, i)) c_prev(1, edges(2, i))], [c(2, edges(1, i)) c_prev(2, edges(2, i))], ...
            'LineStyle', '-');
    end
    
    hold off
    grid minor
    
    fig(2);
    hold on
    plot(car(1), car(2), 'w.');
    if isempty(cw_hdl_y)
        cw_hdl_y = plot(CW(1, C(3, :) == 0), CW(2, C(3, :) == 0), 'y.');
        cw_hdl_b = plot(CW(1, C(3, :) == 1), CW(2, C(3, :) == 1), 'b.');
    else
        cw_hdl_y.XData = CW(1, C(3, :) == 0);
        cw_hdl_y.YData = CW(2, C(3, :) == 0);
        cw_hdl_b.XData = CW(1, C(3, :) == 1);
        cw_hdl_b.YData = CW(2, C(3, :) == 1);
    end
    
    hold off
    
    drawnow;
    c_prev = c;
%         break
    %     pause
end
