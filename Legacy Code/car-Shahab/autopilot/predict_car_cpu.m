function traj = predict_car_cpu(x, C, cfg, dt)
traj = zeros(9, size(C, 2));
for i = 1:size(traj, 2)
    x = car_sim(x, C(:, i), cfg, dt);
    traj(:, i) = x;
end
