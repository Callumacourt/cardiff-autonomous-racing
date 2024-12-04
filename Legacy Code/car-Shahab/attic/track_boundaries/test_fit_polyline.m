[inner, outer] = im2cones('data/track2.png');
inner = inner(:, 1:2:end) * 3;
outer = outer(:, 1:2:end) * 3;
track_width = 5;
cone_dist = 7;

keep = 0.25;
idx = randperm(size(inner, 2));
inner(:, idx(1:round(size(inner, 2) * keep))) = [];
idx = randperm(size(outer, 2));
outer(:, idx(1:round(size(outer, 2) * keep))) = [];

outer = [outer rand(2, 10) * 80];
inner = [inner rand(2, 10) * 80];

x = outer(1, :);
y = outer(2, :);
k = 10;

% [X0, Y0, a, b, c, d] = fit_ef(x, y, k);
% [xn, yn] = ef2xy(X0, Y0, a, b, c, d, linspace(0, 2*pi, numel(x)));
% 
% d = sum(vnorm([x - xn; y - yn]))


Dinner = distance(inner, inner);
Cinner = Dinner < (cone_dist * 1.1);

figure(1); clf;
hold on
% plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b');
plot(inner(1, :), inner(2, :), 'bo');
% plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'g');
plot(outer(1, :), outer(2, :), 'go');

for i = 1:size(Cinner, 1)
    c = find(Cinner(i, :));
    for j = 1:numel(c)
        plot([inner(1, i) inner(1, c(j))], [inner(2, i) inner(2, c(j))], 'k');
    end
end

% plot(xn, yn, 'b');
% plot(xn, yn, 'bo');


hold off
return

% edges_inner = fit_polyline(inner, 'method', 'tsp');
edges_outer = fit_polyline(outer, @objfun, 'method', 'tsp');

figure(2); clf;
hold on
plot(inner(1, :), inner(2, :), 'bo');
I = inner;
for i = 1:size(edges_inner, 1)
    plot([I(1, edges_inner(i, 1)) I(1, edges_inner(i, 2))], [I(2, edges_inner(i, 1)) I(2, edges_inner(i, 2))], 'b');
end
plot(outer(1, :), outer(2, :), 'go');
I = outer;
for i = 1:size(edges_outer, 1)
    plot([I(1, edges_outer(i, 1)) I(1, edges_outer(i, 2))], [I(2, edges_outer(i, 1)) I(2, edges_outer(i, 2))], 'g');
end
hold off

function totalDist = objfun(pop, xy, dmat)

popSize = size(pop, 1);

totalDist = zeros(1,popSize);
k = 20;
for p = 1:popSize
    x = xy(pop(p, :), 1)';
    y = xy(pop(p, :), 2)';
    [X0, Y0, a, b, c, d] = fit_ef(x, y, k);
    [xn, yn] = ef2xy(X0, Y0, a, b, c, d, linspace(0, 2*pi, numel(x)));
    d = sum(vnorm([x - xn; y - yn]));
    totalDist(p) = d;
end
% popSize = size(pop, 1);
n = size(pop, 2);
% totalDist = zeros(1,popSize);
for p = 1:popSize
    d = dmat(pop(p,n),pop(p,1)); % Closed Path
    for k = 2:n
        thisd = dmat(pop(p,k-1),pop(p,k));
%         if thisd > 15
%             thisd = 10000;
%         end
        d = d + thisd;
    end
    totalDist(p) = d;
end
end