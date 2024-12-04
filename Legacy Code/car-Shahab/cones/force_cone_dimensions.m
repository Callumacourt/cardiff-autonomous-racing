function [h, w] = force_cone_dimensions(h, w)

avg = [28.9222; 23.4746];
B = [-0.7721; -0.6355];

f = addcol(B * (B' * subcol([h(:) w(:)]', avg)), avg);
h = f(1, :);
w = f(2, :);
