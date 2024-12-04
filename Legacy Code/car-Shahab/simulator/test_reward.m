w = 256; h = 256;

name = 'track4';
[X, Y] = meshgrid(1:w, 1:h); XX = [X(:) Y(:)]';
[inner, outer] = im2cones(['data/' name '.png']);
inner = inner * 10;
inner = bsxfun(@plus, inner, [w/2; h/2] - mean(inner, 2));
outer = outer * 10;
outer = bsxfun(@plus, outer, [w/2; h/2] - mean(outer, 2));

invert = false;

if invert
    t = inner;
    inner = outer;
    outer = t;
end


pinner = [inner; [inner(:, 2:end) inner(:, 1)]];
pouter = [outer; [outer(:, 2:end) outer(:, 1)]];
%
Di = reshape(polydist(pinner, XX), h, w);
Do = reshape(polydist(pouter, XX), h, w);
D = min(Di, Do);

ini = inpolygon(XX(1, :), XX(2, :), inner(1, :), inner(2, :));
ino = inpolygon(XX(1, :), XX(2, :), outer(1, :), outer(2, :));

if invert
    C = reshape(~ino & ini, h, w);
else
    C = reshape(ino & ~ini, h, w);
end
Bi = bwperim(reshape(ini, h, w));
Bo = bwperim(reshape(ino, h, w));


xi = XX(1, Bi(:));
yi = XX(2, Bi(:));
xo = XX(1, Bo(:));
yo = XX(2, Bo(:));

xx = [xi, xo];
yy = [yi, yo];

% fig(1); clf;
% whitebg('black');
% hold on
% sc(Bi * 0.5 + Bo);
% plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b', 'LineWidth', 1);
% plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'y', 'LineWidth', 1);
% plot(xi, yi, 'g.');
% hold off
% xlim([0 w]); ylim([0 h]);
% axis equalphase_amp_err_mono.pdf

Fx = zeros(h, w);
Fy = zeros(h, w);
poly = [pinner pouter];

BD = zeros(size(poly, 2), size(xx, 2));
for i = 1:size(BD, 1)
    BD(i, :) = psdist(poly(1:2, i), poly(3:4, i), [xx; yy]);
end

for i = 1:numel(xx)
    [~, argmin] = min(BD(:, i));
    if invert
        vec = -poly(3:4, argmin) + poly(1:2, argmin);
    else
        vec = poly(3:4, argmin) - poly(1:2, argmin);
    end
    vec = vec ./ vnorm(vec);
    Fx(yy(i), xx(i)) = vec(1);
    Fy(yy(i), xx(i)) = vec(2);
end

% fig(2); clf;
% sc(cat(3, Fx, Fy), 'flow');

Fxi = inpaint(Fx, ~(Bi | Bo)) .* double(C);
Fyi = inpaint(Fy, ~(Bi | Bo)) .* double(C);
fig(3); clf;
I = sc(cat(3, Fxi, Fyi), 'flow');
sc(1 - I);
hold on
plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b', 'LineWidth', 1);
plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'y', 'LineWidth', 1);
quiver(X(1:4:end, 1:4:end), Y(1:4:end, 1:4:end), Fxi(1:4:end, 1:4:end), Fyi(1:4:end, 1:4:end), 'w');
hold off

dist = D;
dist(~C) = -dist(~C);

fig(4); clf;
sc(dist, jet);
hold on
plot([inner(1, :) inner(1, 1)], [inner(2, :) inner(2, 1)], 'b', 'LineWidth', 1);
plot([outer(1, :) outer(1, 1)], [outer(2, :) outer(2, 1)], 'y', 'LineWidth', 1);
quiver(X(1:4:end, 1:4:end), Y(1:4:end, 1:4:end), Fxi(1:4:end, 1:4:end), Fyi(1:4:end, 1:4:end), 'w');
hold off

track = struct;
track.fx = Fxi;
track.fy = Fyi;
track.dist = dist;
track.inner = inner;
track.outer = outer;
track.name = name;
if invert
    save([track.name 'inv.mat'], '-struct', 'track', '-v6');
else
    save([track.name '.mat'], '-struct', 'track', '-v6');
end

