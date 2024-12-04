function dxdt = derivative(x, dt)
% Compute numerical derivative of a discretised signal.
% Samples must be equally spaced. Each row corresponds to a sample.

dxdt = zeros(size(x));

% Handle boundary cases with one-sided difference.
dxdt(1, :) = (x(2, :) - x(1, :)) / dt;
dxdt(end, :) = (x(end, :) - x(end - 1, :)) / dt;

% Handle the general case
dxdt(2:end - 1, :) = (x(3:end, :) - x(1:end - 2, :)) / (2 * dt);
