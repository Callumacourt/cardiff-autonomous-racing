cfg = load('car_model.mat'); cfg = cfg.cfg;
X = [0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0];
K = 1024;
T = 150;
lambda = 1;
noise_sigma = 0.003;
whitebg('black')

dt = 0.05;
fs = 1.0 / dt;
fc = 0.5;
[fb, fa] = butter(6, fc / (fs * 0.5));
%set polynomials
dF = zeros(2, 6);
f = 0;
XX = [];
deg = 4;

kernel = parallel.gpu.CUDAKernel('predict_car.ptx', 'predict_car.cu', 'predict_car');
tbs = kernel.MaxThreadsPerBlock;
kernel.ThreadBlockSize = [tbs, 1, 1];
kernel.GridSize = [ceil(K / tbs), 1];

cfg_gpu = gpuArray(single(cfg));

traj_h = inf(1, K);
car_h = [];
fig(1); clf; 
plot(50, 50, 'g+', 'MarkerSize', 20);
grid minor;

TRAJ = zeros(9, T, K, 'single', 'gpuArray');
while true
    fig(1);
    hold on
    
    cost = zeros(1, K);
    noise = randn(size(dF, 1), size(dF, 2), K) * noise_sigma;
    
%     TRAJ_CPU = zeros(9, T, K);

    dFn = zeros(2, 6, K);
    
    %apply noise
    for k = 1:K
        dFn(:, :, k) = dF + noise(:, :, k);
    end
    
    % find the control sequences created by the polynomials
    Fn = zeros(2, T, K);
    for k = 1:K
        for i = 1:2
            if i == 1
                Fn(i, :, k) = polyval(dFn(i, :, k), (1:T)) + X(end - 1);
            else
                Fn(i, :, k) = polyval(dFn(i, :, k), (1:T)) + X(end);
            end
        end
    end
    
    % Preciction on CPU
    %     tic
    %     for k = 1:K
    %         TRAJ_CPU(:, :, k) = predict_car_cpu(X, Fn(:, :, k), cfg, dt);
    %     end
    %     toc
    
    Fn_gpu = gpuArray(single(Fn));%zeros(2, T, K, 'single', 'gpuArray');
    % Prediction on GPU
%         tic
    TRAJ = feval(kernel, int32(K), int32(T), gpuArray(single(X)), Fn_gpu, cfg_gpu, single(dt), TRAJ);
    TRAJ = gather(TRAJ);
    
    %     toc
    
    %     return
    
    %cost
    for k = 1:K
        cost(k) = traj_cost(TRAJ(:, :, k), Fn(:, :, k));
        if mod(k - 8, 16) == 0
            if isinf(traj_h(k))
                traj_h(k) = plot(TRAJ(1, :, k), TRAJ(2, :, k), 'Color', [1 1 1 0.15 * 1024/K]);
            else
                set(traj_h(k), 'XData', TRAJ(1, :, k));
                set(traj_h(k), 'YData', TRAJ(2, :, k));
            end
        end
    end
    %weight
    beta = min(cost);
    
    % get index of the corresponding beta
    for i = 1:K
        if beta == cost(i)
            index = i;
        end
    end
    
    dF = dFn(:, :, index);
    
    %create the optimal control sequence
    xsum = polyval(dF(1, :), (1:T));
    ysum = polyval(dF(2, :), (1:T));
    
    %update the controls
    F = [xsum + X(end - 1); ysum + X(end)];
    traj = predict_car_cpu(X, F, cfg, dt);
    
    
    fig(2);
    clf;
    hold on
    plot(max(-1, min(1, cumsum(dF(1, :)) + X(end-1))), 'b');
    plot(max(0, min(1, cumsum(dF(2, :)) + X(end))), 'r');
%     plot(cumsum(dF(2, :)) + X(end), 'r');
    hold off
    ylim([-3 3]);
    grid minor
    
    XX = [XX X];
    fig(3); clf;
    plot(XX(3:end-2, :)');
    legend('vx', 'vy', 'ax', 'ay', 'hdg', 'vhdg', 'ahdg');
    grid minor
    
    fig(1);
    car_w = 1.3; car_l = 4;
    car_body = [car_l/2  car_l/2 -car_l/2 -car_l/2  car_l/2;
        -car_w/2 car_w/2  car_w/2 -car_w/2 -car_w/2];
    car_body_t = rot(X(7)) * car_body + [X(1); X(2)];

    
    if isempty(car_h)
        car_h = plot(car_body_t(1, :), car_body_t(2, :), 'b', 'LineWidth', 4);
        best_traj_h = plot(traj(1, :), traj(2, :), 'r');

    else
        car_h.XData = car_body_t(1, :);
        car_h.YData = car_body_t(2, :);
        set(best_traj_h, 'XData', traj(1, :));
        set(best_traj_h, 'YData', traj(2, :));
    end

    hold off
    axis([-10 70 -10 70]);
%     grid minor
    drawnow;
    
        export_fig(sprintf('out/%06d.png', f), '-png');
    f = f + 1;
    
    
    Fcmd = dF(:, 1) + X(end-1:end);
    dF = [dF(:, 2:end) dF(:, end)];
    
    X = car_sim(X, Fcmd, cfg, dt);
    X = [X; Fcmd];
end

function cost = traj_cost(traj, F)
x = traj(1, :);
y = traj(2, :);
dot_prod = abs(traj(1,150) + traj(2,150))/sqrt(2);
% vx = traj(3, :);
% vy = traj(4, :);
% speed = sqrt(vx.^2 + vy.^2);
cost = mean((x - 50).^2 + (y - 50).^2 + 100*F(2, :).^2) + 1000*dot_prod;
%disp((x-50).^2);
%disp((y-50).^2);
%disp(0.001*f.^2);
%disp(cost)
% cost = sum(1000 * x.^2 + (da - 10).^2);
%      (50*x(end).^2 + 100*(abs(cos(a(end)) + 1)) + 1*dx(end).^2 + 15*da(end).^2);
end