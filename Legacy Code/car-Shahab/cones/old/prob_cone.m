function [P] = prob_cone(h, w, template, table, pix, im)


idx = pix(:, 1) * 65536 + pix(:, 2) * 256 + pix(:, 3);
% prob = pdf(gmm, imhsv);
prob = table(idx + 1);

P = reshape(prob, h, w);

% P(1:500, :) = 0;
P = P .* template;

