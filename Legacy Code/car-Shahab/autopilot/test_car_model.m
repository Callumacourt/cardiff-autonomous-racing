cfg = load('car_model.mat'); cfg = cfg.cfg;

X = [0; 0; 0; 0; 0; 0; 0; 0; 0];

% figure(1); clf;
% hold on
% for st = linspace(-1, 1, 21)
%     ctr = repmat([st; 1.0; 0.0], 1, 60);
%     traj = predict_car(X, ctr, cfg, 0.05);
%     plot(traj(1, :), traj(2, :));
% end
% hold off

ctr = repmat([0.1; 1.0; 0.0;], 1, 10);
traj = predict_car(X, ctr, cfg, 0.05);
