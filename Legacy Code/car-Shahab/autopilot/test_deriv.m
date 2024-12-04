t = linspace(-2, 2, 201);
dt = mean(diff(t));

x = t .^ 3 + t .^ 2 - 4 * t + 4 * sin(4 * t);
dxa = 3 * t .^ 2 + 2 * t - 4 + 16 * cos(4 * t);
dx2a = 6 * t + 2 - 64 * sin(4 * t);

dxn = derivative(x', dt);
dx2n = derivative2(x', dt);

figure(1); clf;
hold on
plot(t, x);
hold off

figure(2); clf;
hold on
plot(t, dxa);
plot(t, dxn);
hold off


figure(3); clf;
hold on
plot(t, dx2a);
plot(t, dx2n);
hold off
