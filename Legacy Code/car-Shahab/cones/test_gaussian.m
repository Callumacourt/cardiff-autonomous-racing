im = zeros(480, 640);

ctr = [100; 200];
sigma = 23;
S = [sigma 0; 0 sigma];

[x, y] = meshgrid(1:size(im, 2), 1:size(im, 1));
X = [x(:) y(:)]';

coeff_norm = 1 / (2 * pi * sigma);
coeff_exp = -0.5 / sigma;
d2 = ((x - ctr(1)) .^2 + (y - ctr(2)) .^ 2);
G = coeff_norm * exp(coeff_exp * d2);

fig(1);
sc(G, inferno);

