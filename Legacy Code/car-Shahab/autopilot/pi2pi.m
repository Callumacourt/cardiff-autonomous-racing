function x = pi2pi(x)

x = mod(x + pi, 2.0 * pi) - pi;
x(x < -pi) = x(x < -pi) + 2.0 * pi;
x(x > -pi) = x(x > -pi) - 2.0 * pi;
