K = 1024;
T = 400;
lambda = 0.05;
noise_mu = 0;
noise_sigma = 0.05;

fig(1); clf;
xlim([-2 2]);
ylim([-0.5 0.5]);
axis([-1.5 1.5 -0.5 0.5]);
grid minor
hdl = [];

iter = 0;
x = [0; pi * 0.5; 0; 0];
dt = 0.01;

% fig(2); clf;

% n = 10000;
% tic
% traj = pend_predict(x, zeros(1, n), dt, n);
% toc
% fig(1); clf;
% plot(traj');
% legend('x', 'dx', '\phi', 'd\phi')


F = zeros(1, T);

f = 0;
ff = 0;
while true
    % MPPI
    %     tic
    cost = zeros(1, K);
    noise = randn(K, T) * noise_sigma + noise_mu;
    for k = 1:K
        Fn = F + noise(k, :);
        traj = pend_predict(x, Fn, dt);
        cost(k) = traj_cost(traj);
    end
    beta = min(cost);
    [beta; x(1); x(2)]'
    cost = exp(-1/lambda * (cost - beta));
    eta = sum(cost);
    omega = 1/eta * cost;
    F = F + omega * noise;
    Fcmd = F(:, 1);
    F = [F(:, 2:end) F(:, end)];
    
    %     Fcmd = 1;
    %     if abs(x(2) < 0.1)
    %         Fcmd = 1;
    %     end
    dx = pend_dyn(x, Fcmd);
    x = x + dx * dt;
    %     toc
    fig(1);
    hdl = draw(hdl, x, Fcmd);
    if mod(f, 3) == 0
        export_fig(sprintf('out/%06d.png', ff), '-png');
        ff = ff + 1;
    end
    drawnow;
    f = f + 1;
    fig(2);
    clf;
    plot(F);
    ylim([-3 3]);
    grid minor
end



function cost = traj_cost(traj)
x = traj(1, :);
a = traj(2, :);
dx = traj(3, :);
da = traj(4, :);
% cost = mean(100*x.^2 + 50*((cos(a) + 1).^2 + sin(a).^2) + dx.^2 + 15*da.^2);
cost = mean(4000*x.^2 + 100*(abs(cos(a) + 1)) + 0*dx.^2 + 0*da.^2);
% cost = sum(1000 * x.^2 + (da - 10).^2);
%      (50*x(end).^2 + 100*(abs(cos(a(end)) + 1)) + 1*dx(end).^2 + 15*da(end).^2);
end

function traj = pend_predict(x, F, dt)
n = size(F, 2);
traj = zeros(size(x, 1), n);
for i = 1:n
    dx = pend_dyn(x, F(:, i));
    x = x + dx * dt;
    traj(:, i) = x;
end
end


function hdl = draw(hdl, x, F)
pos = x(1);
theta = x(2);
w = 0.1; h = 0.05; len = 0.3;
bx = pos + len * sin(theta); by = -len * cos(theta);
if isempty(hdl)
    hold on
    hdl = [0; 0; 0; 0];
    hdl(1) = rectangle('Position', [pos - w/2, -h/2, w, h]);
    hdl(2) = line([pos bx], [0 by], 'LineWidth', 2);
    hdl(3) = plot(bx, by, '.', 'MarkerSize', 32);
    hdl(4) = plot([pos 0], [pos + F * 0.02 0], 'r', 'LineWidth', 2);
    hold off
else
    set(hdl(1), 'Position', [pos - w/2, -h/2, w, h]);
    set(hdl(2), 'XData', [pos bx], 'YData', [0 by]);
    set(hdl(3), 'XData', [bx], 'YData', [by]);
    set(hdl(4), 'XData', [pos pos + F * 0.02], 'YData', [0 0]);
end
end
