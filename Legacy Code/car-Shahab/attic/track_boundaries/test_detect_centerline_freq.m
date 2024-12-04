

[inner, outer] = im2cones('data/track2.png');
inner = inner(:, 1:2:end) * 3;
outer = outer(:, 1:2:end) * 3;
scale = 1;


% outer = outer / 20 - 2;
track_width = 5;
cone_dist = 8;

% figure(1); clf;
% plot_track(inner, outer, scale, cone_dist);

% Decimate
keep = 0.3;
idx = randperm(size(inner, 2));
inner(:, idx(1:randi(round(size(inner, 2) * keep)))) = [];
idx = randperm(size(outer, 2));
outer(:, idx(1:randi(round(size(outer, 2) * keep)))) = [];

figure(2); clf;
plot_track(inner, outer, scale, cone_dist);
k = boundary(outer(1, :)', outer(2, :)', 0.5);
hold on
plot(outer(1, k), outer(2, k), 'k');
hold off



X0 = 0;
Y0 = 0;
a = [1 0 0 0];
b = [0 0 0 0];
c = [0 0 0 0];
d = [1 0 0 0];

n = [1:numel(a)]';

t = linspace(0, 2*pi, 100);
x = X0 + a * cos(n .* t) + b * sin(n .* t);
y = Y0 + c * cos(n .* t) + d * sin(n .* t);

% figure(1); clf;
% plot(x, y);


kdo = KDTreeSearcher(outer');


k = 2;
X = [0; 0; [1; zeros(k-1, 1); zeros(k * 2, 1); 1; zeros(k-1, 1)]];
options = optimset('Display', 'iter', 'MaxFunEvals', 100000, 'MaxIter', 100000, 'TolX', 1e-8, 'TolFun', 1e-8);
% Xmin = -1 * ones(2 + k*4, 1);
% Xmax = +1 * ones(2 + k*4, 1);

Xmin = -2 * ones(2 * 30, 1);
Xmax = +2 * ones(2 * 30, 1);

x0 = rand(2*10, 1);
% [X, fval] = optimise(@(x) objfn(outer, x), 'minx', Xmin, 'maxx', Xmax, 'budget', 1000000);
% [X, fval] = optimise(@(x) objfn(outer, x), 'method', 'fminsearch', 'x0', x0);

options = optimoptions(@fminunc,'Algorithm','quasi-newton', 'Display', 'iter', 'MaxFunEvals', 100000, 'MaxIter', 100000, 'TolX', 1e-8, 'TolFun', 1e-8);
[x,fval,exitflag,output] = fminunc(@(x) objfn(outer, x),x0,options);


% while k < 10
% [X, fval] = fminsearch(@(x) objfn(outer, kdo, x), X, options);
% X0 = X(1);
% Y0 = X(2);
% coeff = reshape(X(3:end), [], 4);
% a = coeff(:, 1)';
% b = coeff(:, 2)';
% c = coeff(:, 3)';
% d = coeff(:, 4)';
% X = [X0; Y0; a(:); 0; b(:); 0; c(:); 0; d(:); 0];
% end

function c = objfn(outer, coeff)

persistent count

if isempty(count)
    count = 0;
end

X = reshape(coeff, 2, [])';

count = count + 1;
if mod(count, 1000) == 0
fig(2); clf;
for i = 1:size(outer, 2)
    a = outer(:, i);
    b = outer(:, mod(i, size(outer, 2)) + 1);
%     if vnorm(a - b) <= cone_dist
    plot([a(1) b(1)], [a(2) b(2)], 'g');
%     end
end
plot(outer(1, :), outer(2, :), 'go');hold on
plot(X(:, 1), X(:, 2), 'LineWidth', 2);
drawnow;
end
[~, d1] = knnsearch(X, outer', 'K', 3);
[~, d2] = knnsearch(outer', X, 'K', 3);
c = mean(d1(:))*0 + mean(d2(:));
end

function c = objfn_freq(outer, kdt, coeff)
persistent count

if isempty(count)
    count = 0;
end

X0 = coeff(1);
Y0 = coeff(2);
coeff = reshape(coeff(3:end), [], 4);
a = coeff(:, 1)';
b = coeff(:, 2)';
c = coeff(:, 3)';
d = coeff(:, 4)';

k = size(coeff, 1);
n = [1:k]';

t = linspace(0, 2*pi, 100);
x = X0 + a * cos(n .* t) + b * sin(n .* t);
y = Y0 + c * cos(n .* t) + d * sin(n .* t);
X = [x; y]';

count = count + 1;
if mod(count, 1000) == 0
fig(2); clf;
for i = 1:size(outer, 2)
    a = outer(:, i);
    b = outer(:, mod(i, size(outer, 2)) + 1);
%     if vnorm(a - b) <= cone_dist
    plot([a(1) b(1)], [a(2) b(2)], 'g');
%     end
end
plot(outer(1, :), outer(2, :), 'go');hold on
plot(x, y, 'LineWidth', 2);
drawnow;
end
[~, d1] = knnsearch(X, outer');
[~, d2] = knnsearch(outer', X);
c = mean(d1) + mean(d2);

end