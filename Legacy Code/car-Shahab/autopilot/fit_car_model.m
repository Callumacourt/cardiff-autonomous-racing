id_data = load('id_data.mat');
dt = 0.050;
% D = [data d_yaw d2_yaw_n_f speed speed.^2 accel vxc vyc axc ayc];
% 1--3: time, ste, thr,
% 4--9: x, y, vx, vy, ax, ay
% 10:   yaw
%    X = [x, y, vx, vy, ax, ay, hdg, vhdg, ahdg]
X = id_data.train(:, 4:12)';
C = id_data.train(:, 2:3)';

cfg0 = [
%     1000; % mass = cfg(1);
    0.2;  % weight_transfer = cfg(2);
    0.55; % cg_height = cfg(3);
    1.25; % cg_to_front_axle = cfg(4);
    1.25; % cg_to_rear_axle = cfg(5);
    0.3;  % max_steering = cfg(6);
    2.0;  % tire_grip = cfg(7);
    5.0;  % corner_stiffness_front = cfg(8);
    5.2;  % corner_stiffness_rear = cfg(9);
    3000; % engine_force = cfg(10);
    8.0;  % roll_resistance = cfg(11);
    2.5;  % air_resistance = cfg(12);
    1.0;  % inertia = cfg(13);
    0.1;
    ];

global nfc
nfc = 0;
x0 = cfg0;
opt = optimset('MaxFunEvals', 1000, 'MaxIter', 1000, 'TolX', 1e-6, 'TolFun', 1e-6, 'Display', 'iter');
[cfg, val] = fminsearch(@(x) objfn(X, C, x, dt), x0, opt);
% minx = zeros(size(x0));
% maxx = 2 * x0;
% [cfg, val] = optimise(@(x) objfn(X, C, x, dt), 'minx', minx, 'maxx', maxx);

% traj = predict_car(X(:, 1), C, cfg, dt);
% 
% fig(2); clf;
% hold on
% plot(X(1, 2:end), X(2, 2:end));
% plot(traj(1, 1:end-1), traj(2, 1:end-1));
% hold off
% axis ij
% drawnow;

function cost = objfn(X, C, cfg, dt)
% tic
global nfc
horz = 100;
step = 10;

n_disp = 1;
if mod(nfc, n_disp) == 0
    fig(1); clf;
    axis ij
    hold on
end
cost = 0;
start = 1;
n = 0;
while true
    last = start + horz - 1;
    if last > size(X, 2), break; end
    x = X(:, start:last);
    c = C(:, start:last);
    traj = predict_car_cpu(x(:, 1), c, cfg, dt);
    
    d = sum((x(:, 2:end) - traj(:, 1:end-1)) .^ 2, 1);
    cost = cost + mean(d); %mean(d .* linspace(1, 0, numel(d)));
    if mod(nfc, n_disp) == 0
        plot(x(1, 2:end), x(2, 2:end), 'b', 'LineWidth', 1);
        plot(traj(1, 1:end-1), traj(2, 1:end-1), 'r');
    end
    n = n + 1;
    start = start + step;
end
cost = cost / n;
if mod(nfc, n_disp) == 0
    hold off
    axis([-100 100 100 300])
    drawnow;
    export_fig(sprintf('out/optim/%06d.png', nfc));
end
nfc = nfc + 1;
% toc
end

