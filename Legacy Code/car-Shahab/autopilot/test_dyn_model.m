% steering, throttle, lin_vel, lin_vel_side, ang_vel

steering = 0.99;
throttle = 0.1;
state = [steering; throttle; 0; 0; 0];

theta = pi / 2;
x = 0;
y = 0;

figure(1); clf;
hold on
dt = 0.050;
for t = 1:1000
    p = sim(net, state);
    state(3:end) = p;
    p'
    sn = sin(theta);
    cs = cos(theta);
    vx = cs * state(3) - sn * state(4);
    vy = sn * state(3) + cs * state(4);
    theta = theta - state(5) ;
    x = x + vx * dt;
    y = y + vy * dt;
    plot(x, y, 'b*');

end
hold off
axis equal
