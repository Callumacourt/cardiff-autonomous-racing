function [X0, Y0, a, b, c, d] = fit_ef(x, y, k)

n = [1:k]';
t = linspace(0, 2*pi, numel(x));


cnt = cos(n .* t);
snt = sin(n .* t);
A = [cnt' snt'];
A = [A ones(size(A, 1), 1)];

coeff = A \ x(:);
a = coeff(1:k);
b = coeff(k+1:end-1);
X0 = coeff(end);

coeff = A \ y(:);
c = coeff(1:k);
d = coeff(k+1:end-1);
Y0 = coeff(end);