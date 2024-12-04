cfg = load('car_model.mat'); cfg = cfg.cfg;
X = [0; 0; 0; 0; 0; 0; 0; 0; 0; 0; 0];

K = 1;

kernel = parallel.gpu.CUDAKernel('predict_car.ptx', 'predict_car.cu', 'predict_car');
tbs = kernel.MaxThreadsPerBlock;
kernel.ThreadBlockSize = [tbs, 1, 1];
kernel.GridSize = [ceil(K / tbs), 1];

cfg_gpu = gpuArray(single(cfg));

T = 10000;
% F = repmat([0.5; 1], 1, T);
F = rand(2, T);

F_gpu = gpuArray(single(F));%zeros(2, T, K, 'single', 'gpuArray');
dt = 0.05;
TRAJ = zeros(9, T, K, 'single', 'gpuArray');
TRAJ = feval(kernel, int32(K), int32(T), gpuArray(single(X)), F_gpu, cfg_gpu, single(dt), TRAJ);
TRAJ = gather(TRAJ);

traj = predict_car_cpu(X, F, cfg, dt);
figure(1); clf;

plot(TRAJ(1:2, :)' - traj(1:2, :)');
% hold on
% plot(traj(1:2, :)');
% hold off
max(max(abs(TRAJ - traj)))
