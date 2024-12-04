function plot_track(inner, outer, scale, cone_dist)

hold on
% plot([inner(1, :) inner(1, 1)] * scale, [inner(2, :) inner(2, 1)] * scale, 'b');
for i = 1:size(inner, 2)
    a = inner(:, i);
    b = inner(:, mod(i, size(inner, 2)) + 1);
    if vnorm(a - b) <= cone_dist
    plot([a(1) b(1)] * scale, [a(2) b(2)] * scale, 'b');
    end
end
plot(inner(1, :) * scale, inner(2, :) * scale, 'bo');
% plot([outer(1, :) outer(1, 1)] * scale, [outer(2, :) outer(2, 1)] * scale, 'g');
for i = 1:size(outer, 2)
    a = outer(:, i);
    b = outer(:, mod(i, size(outer, 2)) + 1);
    if vnorm(a - b) <= cone_dist
    plot([a(1) b(1)] * scale, [a(2) b(2)] * scale, 'g');
    end
end
plot(outer(1, :) * scale, outer(2, :) * scale, 'go');
axis ij
hold off
