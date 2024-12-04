% x^3 + x * (1 - 2*y0)/2 - x0/2 = 0

[xx, yy] = meshgrid(linspace(-4, 4, 256), linspace(-2, 6, 256));
X = [xx(:) yy(:)]';

x0 = X(1, :);
y0 = X(2, :);

p = (1 - 2*y0) / 2;
q = -x0 / 2;
P = [ones(size(q)); zeros(size(q)); p; q];
x = zeros(3, size(P, 2));
for i = 1:size(P, 2)
    x(:, i) = roots(P(:, i));
end

a = 0; b = p; c = q;
Q = (a.^2 - 3*b) / 9;
R = (2*a.^3 - 9 * a.*b + 27 * c) / 54;
% t = sqrt(q.^2 / 4 + p.^3 / 27);
% a = (-q/2 + t).^(1/3);
% b = (-q/2 - t).^(1/3);
% 
% x = a + b;

% D = zeros(1, size(x, 2));
% for i = 1:numel(D)
%     d = sqrt((x(:, i) - x0(:, i)).^2 + (x(:, i).^2 - y0(:, i)).^2);
%     real_roots = [];
%     for j = 1:3
%         if abs(imag(d(j))) < 1e-14
%             real_roots = [real_roots; d(j)];
%         end
%     end
%     D(i) = min(real_roots);
% end
% D = reshape(D, size(xx));
% figure(1);
% sc(D, jet);

