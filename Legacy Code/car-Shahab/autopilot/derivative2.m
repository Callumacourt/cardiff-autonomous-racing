function deriv = derivative2(x, dt)
% Compute second numerical derivative of a discretised signal.
% Samples must be equally spaced. Each row corresponds to a sample.

deriv = zeros(size(x));

dt = dt * dt;

% Handle boundary cases with one-sided difference.
deriv(1, :) = (x(1, :) - 2 * x(2, :) + x(3, :)) / dt;
deriv(end, :) = (x(end - 2, :) - 2 * x(end - 1, :) + x(end, :)) / dt;

% Handle the general case
deriv(2:end - 1, :) = (x(3:end, :) - 2 * x(2:end - 1, :) + x(1:end - 2, :)) / dt;
