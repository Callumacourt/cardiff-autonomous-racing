data_orig = csvread('id_testing.csv');
% 1--4:   time, ste, thr, brk,
% 5--13:  x, y, z, vx, vy, vz, ax, ay, az,
% 14--17: qw, qx, qy, qz,
% 18--23: pitch, roll, yaw, wx, wy, wz

% Fix the problem with the yaw angle going through -pi/pi boundaries
data_orig(:, 20) = accumulate_angle(data_orig(:, 20));


% Resample at regular time intervals
t_orig = (data_orig(:, 1) - data_orig(1, 1)) * 1e-6;
dt = 50;
t_new = (0:50:max(t_orig))';

data_interp = [t_new interp1(t_orig, data_orig(:, 2:end), t_new)];

% Simplified representation
data = data_interp(:, [1 2 3 5 6 8 9 11 12 20]);
% 1--3: time, ste, thr,f
% 4--9: x, y, vx, vy, ax, ay
% 10:   yaw


% Compute angular derivatives
d_yaw_n = derivative(data(:, 10), dt / 1000);
d2_yaw_n = derivative2(data(:, 10), dt / 1000);


% Repair errors in the angular velocity due to discontinuities
disc = find(abs(data_interp(:, 23) - d_yaw_n) > 2);
d_yaw = data_interp(:, 23);
d_yaw(disc) = d_yaw_n(disc);

% Filter angular acceleration
d2_yaw_n_f = medfilt1(d2_yaw_n, 5);

% Derived quantities
vx = data(:, 6);
vy = data(:, 7);
speed = sqrt(vx .* vx + vy .* vy);
ax = data(:, 8);
ay = data(:, 9);
accel = sqrt(ax .* ax + ay .* ay);

% Car-centric quantities
yaw = data(:, 10);
sn = sin(yaw); cs = cos(yaw);
vxc = cs .* vx + sn .* vy;
vyc = cs .* vy - sn .* vx;
axc = cs .* ax + sn .* ay;
ayc = cs .* ay - sn .* ax;

D = [data d_yaw d2_yaw_n_f speed speed.^2 accel vxc vyc axc ayc];
% 1--3: time, ste, thr,
% 4--9: x, y, vx, vy, ax, ay
% 10:   yaw

writematrix(D, 'id_testing_int.csv');

idx = 2650:2700;
figure(1); clf;
hold on
% plot(d_yaw(idx))
% plot(d_yaw_n(idx) * 1000)
% plot(data(idx, 10))
plot(d_yaw(idx))
plot(d2_yaw_n(idx), '--')
plot(d2_yaw_n_f(idx), 'k', 'LineWidth', 2)
hold off
grid minor
