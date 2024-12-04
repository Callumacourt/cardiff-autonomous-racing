% cfg = [
%     1000; % mass = cfg(1);
%     9.81; % gravity = cfg(2);
%     0.2;  % weight_transfer = cfg(3);
%     0.55; % cg_height = cfg(4);
%     1.25; % cg_to_front_axle = cfg(5);
%     1.25; % cg_to_rear_axle = cfg(6);
%     0.3;  % max_steering = cfg(7);
%     2.0;  % tire_grip = cfg(8);
%     5.0;  % corner_stiffness_front = cfg(9);
%     5.2;  % corner_stiffness_rear = cfg(10);
%     10000;% brake_force = cfg(11);
%     3000; % engine_force = cfg(12);
%     8.0;  % roll_resistance = cfg(13);
%     2.5;  % air_resistance = cfg(14);
%     1.0;  % inertia = cfg(15);
%     ];
load car_model.mat
X = zeros(9, 1);
figure(1); clf;
set(gcf, 'windowkeypressfcn', @on_key);
h = plot(X(1), X(2), '*');
len = 10;
hl = line([X(1) X(1) + len * cos(X(7))], [X(2) X(2) + len * sin(X(7))]);
xlim([-50 50]);
ylim([-50 50]);
axis ij
grid minor
while true
    t = tic;
    
    X = car_sim(X, [-1.0; 0.5; 0], cfg, 0.05);
    X(1:3)'
    h.XData = X(1);
    h.YData = X(2);
    hl.XData = [X(1) X(1) + len * cos(X(7))];
    hl.YData = [X(2) X(2) + len * sin(X(7))];
    
    while toc(t) < 0.05
        pause(0.01);
    end
    %     toc(t);
end
function on_key(src, evt)
key = evt.Key;
src
key
end

