cones = load('cones_4_labelled.txt');
whitebg('black');


cfg = load('car_model.mat'); cfg = cfg.cfg;
cfg(11) = 0;
X = [-18.25; 30; 0; 0; 0; 0; deg2rad(110); 0; 0; 0; 0];
% X = [0; 0; 0; 0; 0; 0; deg2rad(110); 0; 0; 0; 0];
K = 1024;
T = 200;
lambda = 1;
noise_sigma = 0.003;
dt = 0.05;
kernel = parallel.gpu.CUDAKernel('predict_car.ptx', 'predict_car.cu', 'predict_car');
tbs = kernel.MaxThreadsPerBlock;
kernel.ThreadBlockSize = [tbs, 1, 1];
kernel.GridSize = [ceil(K / tbs), 1];
cfg_gpu = gpuArray(single(cfg));
cost = zeros(1, K);

dF = zeros(2, T);
traj_h = inf(1, K);


labels = cones(:, 1)';
cones = cones(:, 2:3)';
[tri, edges_y, edges_b] = find_track_boundaries([cones; labels - 1]);
edges_all = [edges_y edges_b];

car_w = 1.3; car_l = 3.5;
car_h = [];

fov = 65;
fovv = fov * 720 / 1280;
height = 2; % Height of cameras AGL
range_min = height / tan(deg2rad(fovv / 2));
range_min_side = range_min / cos(deg2rad(fov / 2));
range_max = 17 / cos(deg2rad(fov / 2));
fwd = [1; 0];
frustum = [rot(-deg2rad(fov / 2)) * fwd * range_max, ...
    rot(-deg2rad(fov / 2)) * fwd * range_min_side, ...
    rot(deg2rad(fov / 2)) * fwd * range_min_side, ...
    rot(deg2rad(fov / 2)) * fwd * range_max] + [1.5; 0];

TRAJ = zeros(9, T, K, 'single', 'gpuArray');
% TRAJ = zeros(9, T, K, 'single');
f = fig(1); clf;

% subplot(1, 3, 3);
hold on
plot(cones(1, labels == 1), cones(2, labels == 1), 'y.', 'MarkerSize', 8);
plot(cones(1, labels == 2), cones(2, labels == 2), '.', 'Color', [0.2 0.5 1.0], 'MarkerSize', 8);
        plot([cones(1, edges_y(1, :)); cones(1, edges_y(2, :))], ...
            [cones(2, edges_y(1, :)); cones(2, edges_y(2, :))], 'y');
        plot([cones(1, edges_b(1, :)); cones(1, edges_b(2, :))], ...
            [cones(2, edges_b(1, :)); cones(2, edges_b(2, :))], 'Color', [0.2 0.5 1.0]);
hold off
axis equal
axis([-50 50 -100 100]);
grid minor
a = gca;
% subplot(1, 3, 1:2);
% axis([-15 15 -5 25]);
% grid minor

frame = 0;
while true
    car_pos = X(1:2);
    car_hdg = X(7);
    car_rot = rot(car_hdg);
    
    world_to_car = inv([[rot(car_hdg - pi/2) car_pos]; [0 0 1]]); world_to_car = world_to_car(1:2, :);
    cones_local = world_to_car * [cones; ones(1, size(cones, 2))];
    angle = atan2(cones_local(2, :), cones_local(1, :));
    in_frustum = (angle < pi/2 + deg2rad(fov / 2)) & (angle > pi/2 - deg2rad(fov / 2));
    distance = vnorm(cones_local);
    in_range = distance > range_min & distance < range_max;
    cones_local(:, ~(in_frustum & in_range)) = [];
    labels_local = labels(in_frustum & in_range) - 1;
    
    %     [tri, edges_y, edges_b, cline, cline_i, centre, evec, V, xx, yy] = analyse_track_local([cones_local; labels_local]);
    
    noise = randn(size(dF, 1), T, K) * noise_sigma;
    
    Fn = zeros(2, T, K);
    
    for k = 1:K
        dFn = dF + noise(:, :, k);
        Fn(:, :, k) = [cumsum(dFn(1, :)) + X(end - 1); cumsum(dFn(2, :)) + X(end)];
    end
    
    Fn_gpu = gpuArray(single(Fn));
    TRAJ = feval(kernel, int32(K), int32(T), gpuArray(single(X)), Fn_gpu, cfg_gpu, single(dt), TRAJ);
    TRAJ = gather(TRAJ);
    %         for k = 1:K
    %             TRAJ(:, :, k) = predict_car_cpu(X, Fn(:, :, k), cfg, dt);
    %         end
    %
    for k = 1:K
        cost(k) = traj_cost(TRAJ(:, :, k), Fn(:, :, k), cones, labels, edges_all);
    end
    
    beta = min(cost);
    cost = exp(-1/lambda * (cost - beta));
    eta = sum(cost);
    omega = 1/eta * cost;
    for k = 1:K
        dF = dF + omega(k) * noise(:, :, k);
    end
    
    F = [cumsum(dF(1, :)) + X(end - 1); cumsum(dF(2, :)) + X(end)];
    traj = predict_car_cpu(X, F, cfg, dt);
    
    
    
    
    fig(1);
%     subplot(1, 3, 3);
    hold on
    plot(cones(1, labels == 1), cones(2, labels == 1), 'y.', 'MarkerSize', 8);
    plot(cones(1, labels == 2), cones(2, labels == 2), '.', 'Color', [0.2 0.5 1.0], 'MarkerSize', 8);
    car_h = plot_car(car_h, car_pos, car_rot, car_w, car_l, frustum);
    for k = 1:K
        if mod(k - 8, 16) == 0
            if isinf(traj_h(k))
                traj_h(k) = plot(TRAJ(1, :, k), TRAJ(2, :, k), 'Color', [1 1 1 0.15 * 1024/K]);
            else
                set(traj_h(k), 'XData', TRAJ(1, :, k));
                set(traj_h(k), 'YData', TRAJ(2, :, k));
            end
        end
    end
    
    hold off
    
    %     grid minor
    
    
    if 0
    subplot(1, 3, 1:2);
    hold on
        Vx = reshape(V(1, :), size(xx));
        Vy = reshape(V(2, :), size(xx));
        quiver(xx, yy, Vx, Vy, 'Color', [0.1 0.5 0.0], 'LineWidth', 2);
        
        triplot(tri', cones_local(1, :), cones_local(2, :), 'w:');
        
        for i = 1:size(edges_y, 2)
            line([cones_local(1, edges_y(1, i)) cones_local(1, edges_y(2, i))], ...
                [cones_local(2, edges_y(1, i)) cones_local(2, edges_y(2, i))], 'Color', 'y', 'LineWidth', 2);
        end
        for i = 1:size(edges_b, 2)
            line([cones_local(1, edges_b(1, i)) cones_local(1, edges_b(2, i))], ...
                [cones_local(2, edges_b(1, i)) cones_local(2, edges_b(2, i))], 'Color', 'b', 'LineWidth', 2);
        end
        
        % Centreline
        plot(cline_i(1, :), cline_i(2, :), 'w', 'LineWidth', 2);
        plot(cline(1, :), cline(2, :), 'wo', 'MarkerSize', 5);
        % Prinipal component
        len = 7;
        x0 = centre + len * evec(:, 1);
        x1 = centre - len * evec(:, 1);
        line([x0(1) x1(1)], [x0(2) x1(2)], 'Color', 'r', 'LineStyle', '--');
        
        plot(cones_local(1, labels_local == 0), cones_local(2, labels_local == 0), 'y.', 'MarkerSize', 32);
        plot(cones_local(1, labels_local == 1), cones_local(2, labels_local == 1), '.', 'Color', [0.2 0.5 1.0], 'MarkerSize', 32);
    end
    hold off
    drawnow;
    
    export_fig(sprintf('out/mppi_track/%06d.png', frame));
    frame = frame + 1;
    
    Fcmd = dF(:, 1) + X(end-1:end);
    dF = [dF(:, 2:end) dF(:, end)];
    
    X = car_sim(X, Fcmd, cfg, dt);
    X = [X; Fcmd];
    fprintf('%.2f %.2f\t%.3f\n', X(1), X(2), beta);
end


function h = plot_car(h, pos, R, car_w, car_l, frustum)
car_body = [car_l/2  car_l/2 -car_l/2 -car_l/2  car_l/2;
    -car_w/2 car_w/2  car_w/2 -car_w/2 -car_w/2];
car_body_t = R * car_body + pos;

frustum = R * frustum + pos;
frustum = [frustum frustum(:, 1)];
if isempty(h)
    h(1) = plot(car_body_t(1, :), car_body_t(2, :), 'r', 'LineWidth', 2);
    h(2) = plot(frustum(1, :), frustum(2, :), 'Color', [0.5 0.5 0.5]);
else
    set(h(1), 'XData', car_body_t(1, :));
    set(h(1), 'YData', car_body_t(2, :));
    set(h(2), 'XData', frustum(1, :));
    set(h(2), 'YData', frustum(2, :));
end
end

function cost = traj_cost(traj, F, cones, labels, edges)
x = traj(1, :);
y = traj(2, :);
vx = traj(3, :);
vy = traj(4, :);
speed = sqrt(vx.^2 + vy.^2);
% D = distance(traj(1:2, :), cones);
% cost = mean((x - 15).^2 + (y - 60).^2 + 100*F(2, :).^2) - min(D(:)) * 100;

bnd = [cones(:, edges(1, :)); cones(:, edges(2, :))];
path = [x(1:end-1); y(1:end-1); x(2:end); y(2:end)];
int = seg_int(double(path), bnd);
idx = find(max(int, [], 2), 1);
cost = -mean(speed);
if ~isempty(idx)
% fig(2); clf;
% hold on
% plot(path([1 3], :), path([2 4], :), 'g');
% plot(bnd([1 3], :), bnd([2 4], :), 'w');
% int_path = max(int, [], 2) == 1;
% plot(path([1 3], int_path), path([2 4], int_path), 'r');
% int_bnd = max(int) == 1;
% plot(bnd([1 3], int_bnd), bnd([2 4], int_bnd), 'r');
% hold off
% axis equal
% % sc(int);
% drawnow;
    cost = cost + (1 - (idx / size(path, 2))) * 10000;
end
% cost = sum(1000 * x.^2 + (da - 10).^2);
%      (50*x(end).^2 + 100*(abs(cos(a(end)) + 1)) + 1*dx(end).^2 + 15*da(end).^2);
end
